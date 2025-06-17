import boto3
import mimetypes
import requests
import os
import json
from typing import Dict, List, Union
from io import BytesIO
from urllib.parse import urlencode

from common.app_config import config
from common.app_logger import logger


class S3ClientService:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
            region_name=config.AWS_REGION
        )
        self.bucket_name = config.AWS_S3_BUCKET_NAME
        self.key_prefix = config.AWS_S3_KEY_PREFIX

    def download_file(self, s3_key, local_path) -> None:
        """Download a file from S3 to a local path."""
        self.s3.download_file(self.bucket_name, s3_key, local_path)

    def get_file_content_type(self, s3_key) -> str:
        """Get the content type of a file in S3."""
        metadata = self.get_object_metadata(s3_key)
        return metadata['ContentType']

    def copy_object(self, source_key, dest_key, content_type=None, metadata=None, tagging=None) -> None:
        """
        Copy an object from source_key to dest_key within the same bucket.
        
        Args:
            source_key (str): Source S3 key.
            dest_key (str): Destination S3 key.
            metadata (dict, optional): Custom metadata to set on the copied object.
                                     If not provided, uses metadata from source object.
            tagging (dict, optional): Tags to apply to the copied object.
        """
        copy_source = {
            'Bucket': self.bucket_name,
            'Key': source_key
        }
        
        copy_args = {
            'Bucket': self.bucket_name,
            'CopySource': copy_source,
            'Key': dest_key
        }

        if content_type is not None:
            # Use provided content type
            copy_args['ContentType'] = content_type
        else:
            # Guess content type from source object
            content_type = self.get_file_content_type(source_key)
            copy_args['ContentType'] = content_type
        
        if metadata is not None:
            # Use provided metadata and replace existing metadata
            copy_args['Metadata'] = metadata
            copy_args['MetadataDirective'] = 'REPLACE'
        else:
            # Copy metadata from source object
            copy_args['MetadataDirective'] = 'COPY'
        
        if tagging is not None:
            copy_args['Tagging'] = urlencode(tagging)
            copy_args['TaggingDirective'] = 'REPLACE'
        else:
            copy_args['TaggingDirective'] = 'COPY'
        
        self.s3.copy_object(**copy_args)

    def upload_file(self, file_path, s3_key, content_type=None, metadata=None, tagging=None) -> None:
        """
        Upload the file at file_path to the specified s3_key in the S3 bucket.

        Args:
            file_path (str): Local path to the file.
            s3_key (str): Destination key in S3.
            content_type (str, optional): MIME type of the file. Guessed if not provided.
            metadata (dict, optional): Additional metadata to store with the object.
            tagging (dict, optional): Tags to apply to the object.
        """
        if content_type is None:
            content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        extra_args = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = metadata
        if tagging:
            extra_args["Tagging"] = urlencode(tagging)

        self.s3.upload_file(
            Filename=file_path,
            Bucket=self.bucket_name,
            Key=s3_key,
            ExtraArgs=extra_args
        )

    def upload_from_url(self, url, s3_key, content_type=None, metadata=None) -> None:
        """
        Streams a file from a remote URL and uploads it to S3.

        Args:
            url (str): The remote file URL.
            s3_key (str): Destination S3 key.
            content_type (str, optional): Content type. Will be guessed from response if not provided.
            metadata (dict, optional): Optional metadata to attach to the S3 object.
        """
        response = requests.get(url, stream=True, timeout=900)
        response.raise_for_status()

        content_type = content_type or response.headers.get("Content-Type", "application/octet-stream")
        extra_args = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = metadata

        self.s3.upload_fileobj(
            Fileobj=BytesIO(response.content),
            Bucket=self.bucket_name,
            Key=s3_key,
            ExtraArgs=extra_args
        )

    def get_object_metadata(self, s3_key) -> Dict:
        """
        Retrieve all metadata (system + user-defined) of an object in S3.
        """
        response = self.s3.head_object(Bucket=self.bucket_name, Key=s3_key)

        # Start with system metadata
        metadata = {
            "ContentLength": response.get("ContentLength"),
            "ContentType": response.get("ContentType"),
            "LastModified": response.get("LastModified"),
            "ETag": response.get("ETag"),
            "StorageClass": response.get("StorageClass")
        }

        # Merge in user-defined metadata (if any)
        user_metadata = response.get("Metadata", {})
        metadata.update(user_metadata)
        return metadata

    def get_object_tags(self, s3_key: str) -> dict:
        """
        Retrieve tags of an object in S3.
        
        Args:
            s3_key (str): S3 key of the object.
            
        Returns:
            dict: Dictionary of tags (key-value pairs).
        """
        try:
            response = self.s3.get_object_tagging(Bucket=self.bucket_name, Key=s3_key)
            return {tag['Key']: tag['Value'] for tag in response.get('TagSet', [])}
        except self.s3.exceptions.NoSuchKey:
            # Object doesn't exist or has no tags
            return {}

    def update_metadata(self, s3_key: str, metadata: dict, replace: bool = False) -> None:
        """
        Update metadata for an existing S3 object.
        
        Args:
            s3_key (str): S3 key of the object to update.
            metadata (dict): Metadata to set or merge.
            replace (bool): If True, replace all existing metadata. 
                          If False, merge with existing metadata (upsert).
        """
        if replace:
            # Replace all metadata
            final_metadata = metadata
        else:
            # Merge with existing metadata (upsert)
            response = self.s3.head_object(Bucket=self.bucket_name, Key=s3_key)
            current_user_metadata = response.get("Metadata", {})
            final_metadata = {**current_user_metadata, **metadata}
        
        # Copy object to itself with updated metadata
        self.copy_object(s3_key, s3_key, metadata=final_metadata)

    def update_tags(self, s3_key: str, tags: dict, replace: bool = False) -> None:
        """
        Update tags for an existing S3 object.
        
        Args:
            s3_key (str): S3 key of the object to update.
            tags (dict): Tags to set or merge.
            replace (bool): If True, replace all existing tags. 
                          If False, merge with existing tags (upsert).
        """
        if replace:
            # Replace all tags
            final_tags = tags
        else:
            # Merge with existing tags (upsert)
            try:
                response = self.s3.get_object_tagging(Bucket=self.bucket_name, Key=s3_key)
                current_tags = {tag['Key']: tag['Value'] for tag in response.get('TagSet', [])}
                final_tags = {**current_tags, **tags}
            except self.s3.exceptions.NoSuchKey:
                # Object doesn't exist or has no tags
                final_tags = tags
        
        # Convert dict to TagSet format
        tag_set = [{'Key': k, 'Value': v} for k, v in final_tags.items()]
        
        self.s3.put_object_tagging(
            Bucket=self.bucket_name,
            Key=s3_key,
            Tagging={'TagSet': tag_set}
        )

    def generate_presigned_url(self, s3_key, expiration=3600, filename=None):
        """
        Generate a pre-signed URL for getting an object from S3.

        :param s3_key: str (S3 key)
        :param expiration: int (URL expiration in seconds)
        :param filename: str (optional filename for download)
        :return: str (Pre-signed URL)
        """
        params = {
            'Bucket': self.bucket_name,
            'Key': s3_key
        }
        
        if filename:
            params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'

        return self.s3.generate_presigned_url(
            ClientMethod='get_object',
            Params=params,
            ExpiresIn=expiration
        )

    def upload_json(self, s3_key: str, json_obj_or_list: Union[List, Dict], metadata: dict = None):
        """
        Uploads a Python list or dict as a JSON file to S3 without writing to disk.

        Args:
            s3_key (str): Destination S3 key.
            json_obj_or_list (list, dict): The Python list or dict to upload.
            metadata (dict, optional): Optional metadata for the uploaded object.
        """

        json_bytes = BytesIO(json.dumps(json_obj_or_list).encode("utf-8"))

        extra_args = {
            "ContentType": "application/json"
        }
        if metadata:
            extra_args["Metadata"] = metadata

        self.s3.upload_fileobj(
            Fileobj=json_bytes,
            Bucket=self.bucket_name,
            Key=s3_key,
            ExtraArgs=extra_args
        )
