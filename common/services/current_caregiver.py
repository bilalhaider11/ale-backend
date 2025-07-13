from typing import List, Dict
from datetime import datetime
import botocore.exceptions

from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.current_caregiver import CurrentCaregiver
from common.services.s3_client import S3ClientService
from common.helpers.csv_utils import clean_string, parse_date_string

logger = get_logger(__name__)


class CurrentCaregiverService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.caregiver_repo = None
        self.s3_client = S3ClientService()
        self.bucket_name = config.AWS_S3_BUCKET_NAME
        self.caregivers_prefix = "caregivers-list/"
    
    def delete_all_caregivers(self) -> bool:
        """Delete all existing current caregiver records"""
        logger.info("Deleting all existing current caregiver records...")
        return self.caregiver_repo.truncate_table()
    
    def bulk_import_caregivers(self, rows: List[Dict[str, str]]) -> bool:
        """Import CSV data into current_caregiver table using batch processing"""
        record_count = len(rows)
        logger.info(f"Inserting {record_count} current caregiver records...")
        
        # Process in batches for better performance
        batch_size = 1000
        total_batches = (record_count + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, record_count)
            batch_rows = rows[start_idx:end_idx]
            
            with self.caregiver_repo.adapter:
                for row in batch_rows:
                    record = CurrentCaregiver(
                        caregiver_id=clean_string(row.get('caregiver id')),
                        first_name=clean_string(row.get('first name')),
                        last_name=clean_string(row.get('last name')),
                        address=clean_string(row.get('address')),
                        city=clean_string(row.get('city')),
                        state=clean_string(row.get('state')),
                        postal_code=clean_string(row.get('postal code')),
                        hire_date=parse_date_string(row.get('hire date')),
                        caregiver_tags=clean_string(row.get('caregiver tags')),
                        email=clean_string(row.get('email')),
                        date_of_birth=parse_date_string(row.get('date of birth'))
                    )
                    
                    self.caregiver_repo.insert_caregiver(record)
            
            logger.info(f"Completed batch {batch_num+1}/{total_batches}")
        
        logger.info("Successfully imported current caregiver data")
        return True


    def upload_caregiver_list(self, file_path, original_filename=None):
        """
        Upload a CSV or XLSX file to S3 bucket under caregivers-list/ prefix.
        Creates a timestamped file: caregivers-list/<timestamp>.<extension>
        
        Args:
            file_path (str): Local path to the CSV or XLSX file
            original_filename (str): Original filename to store in metadata
        
        Returns:
            dict: Information about the uploaded file including key and URL
        """
        # Generate timestamp for file naming
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        
        # Determine file extension
        file_extension = '.xlsx' if file_path.lower().endswith('.xlsx') else '.csv'
        
        # Define S3 key for timestamped file
        timestamped_key = f"{self.caregivers_prefix}{timestamp}{file_extension}"

        # Define S3 key for latest file
        latest_key = f"{self.caregivers_prefix}latest"
            
        # Prepare metadata
        metadata = {
            "upload_date": timestamp
        }

        if original_filename:
            metadata["original_filename"] = original_filename
        
        # Upload the file with timestamp name
        self.s3_client.upload_file(
            file_path=file_path,
            s3_key=timestamped_key,
            metadata=metadata
        )

        self.s3_client.copy_object(
            source_key=timestamped_key,
            dest_key=latest_key,
            metadata=metadata,
            tagging={"status": "pending"}
        )

        result = {
            "timestamped_file": {
                "url": self.s3_client.generate_presigned_url(timestamped_key)
            },
            "latest_file": {
                "url": self.s3_client.generate_presigned_url(latest_key)
            }
        }

        return result

