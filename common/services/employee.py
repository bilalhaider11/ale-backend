import os
import datetime
from common.app_config import config
from common.services.s3_client import S3ClientService


class EmployeeService:
    """Service for handling employee-related operations including file uploads."""

    def __init__(self):
        self.s3_client = S3ClientService()
        self.bucket_name = config.AWS_S3_EMPLOYEE_BUCKET_NAME
        self.employees_prefix = "employees-list/"

    def upload_employee_csv(self, file_path):
        """
        Upload a CSV file to S3 bucket under employees-list/ prefix.
        Creates two files:
        1. A timestamped file: employees-list/<timestamp>.csv
        2. A copy named latest.csv: employees-list/latest.csv
        
        Args:
            file_path (str): Local path to the CSV file
        
        Returns:
            dict: Information about the uploaded files including keys and URLs
        """
        # Generate timestamp for file naming
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        
        # Define S3 keys for both versions
        timestamped_key = f"{self.employees_prefix}{timestamp}.csv"
        latest_key = f"{self.employees_prefix}latest.csv"
        
        # Save original bucket
        original_bucket = self.s3_client.bucket_name
        
        try:
            # Set the correct bucket for employee files
            self.s3_client.bucket_name = self.bucket_name
            
            # Upload the file with timestamp name
            self.s3_client.upload_file(
                file_path=file_path,
                s3_key=timestamped_key,
                content_type="text/csv",
                metadata={"upload_date": timestamp}
            )
            
            # Create a copy named latest.csv
            self.s3_client.copy_object(
                source_key=timestamped_key,
                dest_key=latest_key
            )
        finally:
            # Restore original bucket
            self.s3_client.bucket_name = original_bucket

        # Set bucket to employee bucket temporarily for generating URLs
        original_bucket = self.s3_client.bucket_name
        self.s3_client.bucket_name = self.bucket_name
        
        try:
            result = {
                "timestamped_file": {
                    "url": self.s3_client.generate_presigned_url(timestamped_key)
                },
                "latest_file": {
                    "url": self.s3_client.generate_presigned_url(latest_key)
                }
            }
        finally:
            # Restore original bucket
            self.s3_client.bucket_name = original_bucket
            
        return result




