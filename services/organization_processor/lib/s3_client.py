import boto3
import requests
from io import BytesIO
import mimetypes
from urllib.parse import urlparse
from common.app_logger import create_logger
from common.app_config import config

logger = create_logger()

class OrganizationS3Client:
    """S3 client specifically for organization processor operations"""
    
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
            region_name=config.AWS_REGION
        )
        self.bucket_name = config.AWS_S3_LOGOS_BUCKET_NAME
        self.key_prefix = getattr(config, 'AWS_S3_KEY_PREFIX', '')
    
    def upload_from_url(self, url, s3_key, content_type=None, metadata=None):
        """
        Download a file from a URL and upload it to S3
        
        Args:
            url: Source URL
            s3_key: Destination S3 key
            content_type: Content type of the file
            metadata: Metadata to attach to the S3 object
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Downloading file from URL: {url}")
            response = requests.get(url)
            if response.status_code != 200:
                logger.error(f"Failed to download file from URL: {url}, status code: {response.status_code}")
                return False
            
            # Use content type from response if not provided
            if not content_type:
                content_type = response.headers.get('Content-Type')
                
                # If still not available, try to guess from URL
                if not content_type:
                    parsed_url = urlparse(url)
                    path = parsed_url.path
                    content_type, _ = mimetypes.guess_type(path)
                    
                # Default to binary/octet-stream if still not determined
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Prepare the full S3 key with prefix
            full_s3_key = f"{self.key_prefix}{s3_key}" if self.key_prefix else s3_key
            
            # Prepare metadata
            extra_args = {
                'ContentType': content_type,
                'ACL': 'public-read'
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload to S3
            logger.info(f"Uploading file to S3: {full_s3_key}")
            self.s3.upload_fileobj(
                BytesIO(response.content),
                self.bucket_name,
                full_s3_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Successfully uploaded file to S3: {full_s3_key}")
            return True
            
        except Exception as e:
            logger.exception(f"Error uploading file from URL to S3: {e}")
            return False
    
