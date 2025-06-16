from typing import List, Optional
import pandas as pd
from datetime import date, datetime

from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.current_caregiver import CurrentCaregiver
from common.services.s3_client import S3ClientService
from common.app_config import config
from common.helpers.csv_utils import clean_string, parse_date_string

logger = get_logger(__name__)


class CurrentCaregiverService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.caregiver_repo = self.repository_factory.get_repository(RepoType.CURRENT_CAREGIVER, message_queue_name="")
        self.s3_client = S3ClientService()
        self.bucket_name = config.AWS_S3_EMPLOYEE_BUCKET_NAME
        self.caregivers_prefix = "caregivers-list/"
    
    def delete_all_caregivers(self) -> bool:
        """Delete all existing current caregiver records"""
        try:
            logger.info("Deleting all existing current caregiver records...")
            return self.caregiver_repo.truncate_table()
        except Exception as e:
            logger.error(f"Error deleting current caregivers: {str(e)}")
            return False
    
    def bulk_import_caregivers(self, df: pd.DataFrame) -> bool:
        """Import CSV data into current_caregiver table using batch processing"""
        try:
            record_count = len(df)
            logger.info(f"Inserting {record_count} current caregiver records...")
            
            # Process in batches for better performance
            batch_size = 1000
            total_batches = (record_count + batch_size - 1) // batch_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, record_count)
                batch_df = df.iloc[start_idx:end_idx]
                
                with self.caregiver_repo.adapter:
                    for _, row in batch_df.iterrows():
                        record = CurrentCaregiver(
                            caregiver_id=clean_string(row.get('Caregiver ID')),
                            first_name=clean_string(row.get('First Name')),
                            last_name=clean_string(row.get('Last Name')),
                            address=clean_string(row.get('Address')),
                            city=clean_string(row.get('City')),
                            state=clean_string(row.get('State')),
                            postal_code=clean_string(row.get('Postal Code')),
                            hire_date=parse_date_string(row.get('Hire Date')),
                            caregiver_tags=clean_string(row.get('Caregiver Tags')),
                            email=clean_string(row.get('Email')),
                            date_of_birth=parse_date_string(row.get('Date Of Birth'))
                        )
                        
                        self.caregiver_repo.insert_caregiver(record)
                
                logger.info(f"Completed batch {batch_num+1}/{total_batches}")
            
            logger.info("Successfully imported current caregiver data")
            return True
            
        except Exception as e:
            logger.error(f"Error importing CSV data: {str(e)}")
            return False
    
    def upload_caregiver_csv(self, file_path):
        """
        Upload a CSV file to S3 bucket under caregivers-list/ prefix.
        Creates two files:
        1. A timestamped file: caregivers-list/<timestamp>.csv
        2. A copy named latest.csv: caregivers-list/latest.csv
        
        Args:
            file_path (str): Local path to the CSV file
        
        Returns:
            dict: Information about the uploaded files including keys and URLs
        """
        # Generate timestamp for file naming
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        
        # Define S3 keys for both versions
        timestamped_key = f"{self.caregivers_prefix}{timestamp}.csv"
        latest_key = f"{self.caregivers_prefix}latest.csv"
        
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
