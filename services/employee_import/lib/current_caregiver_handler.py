import tempfile
import os
import csv
from common.app_logger import create_logger
from common.services.s3_client import S3ClientService
from common.services.current_caregiver import CurrentCaregiverService

logger = create_logger()

class CurrentCaregiverHandler:
    """Handler for processing caregiver CSV files"""
    
    def __init__(self, config):
        self.config = config
        self.s3_client = S3ClientService()
        self.caregiver_service = CurrentCaregiverService(config)
        
    def process_caregiver_csv(self, bucket, key):
        """
        Process a caregiver CSV file from S3
        
        Args:
            bucket (str): S3 bucket name
            key (str): S3 object key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Skip processing if the file is named latest.csv
            if key.endswith('latest.csv'):
                logger.info(f"Skipping latest.csv file: {bucket}/{key}")
                return True
            # Create a temporary file to download the CSV
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                temp_path = temp_file.name
            
            # Download the file from S3
            original_bucket = self.s3_client.bucket_name
            self.s3_client.bucket_name = bucket
            
            try:
                self.s3_client.download_file(key, temp_path)
            finally:
                self.s3_client.bucket_name = original_bucket
            
            # Read CSV file using csv module
            try:
                with open(temp_path, 'r', encoding='utf-8-sig') as csvfile:
                    reader = csv.DictReader(csvfile)
                    rows = list(reader)
                
                if not rows:
                    logger.warning(f"No caregiver records found in CSV file: {bucket}/{key}")
                    return True
                
                logger.info(f"Found {len(rows)} caregiver records in CSV file")
                
                # Delete existing records
                if not self.caregiver_service.delete_all_caregivers():
                    logger.error("Failed to delete existing caregiver records")
                    return False
                
                # Import new records
                if not self.caregiver_service.bulk_import_caregivers(rows):
                    logger.error("Failed to import caregiver records")
                    return False
                
                logger.info(f"Successfully imported {len(rows)} caregiver records")
                return True
                
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
        except Exception as e:
            logger.exception(f"Error processing caregiver CSV: {str(e)}")
            return False
