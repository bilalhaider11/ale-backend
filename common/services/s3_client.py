import boto3
import os
from common.app_config import config


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

    def download_file(self, s3_key, local_path):
        """Download a file from S3 to a local path."""
        full_s3_key = os.path.join(self.key_prefix, s3_key)
        self.s3.download_file(self.bucket_name, full_s3_key, local_path)
        print(f"Downloaded {full_s3_key} to {local_path}")
