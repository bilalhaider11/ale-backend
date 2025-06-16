from typing import List, Dict
from datetime import datetime

from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.current_employee import CurrentEmployee
from common.services.s3_client import S3ClientService
from common.app_config import config
from common.helpers.csv_utils import clean_string

logger = get_logger(__name__)


class CurrentEmployeeService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.current_employee_repo = self.repository_factory.get_repository(RepoType.CURRENT_EMPLOYEE, message_queue_name="")
        self.s3_client = S3ClientService()
        self.bucket_name = config.AWS_S3_BUCKET_NAME
        self.employees_prefix = "employees-list/"
    
    def delete_all_employees(self) -> bool:
        """Delete all existing current employee records"""
        logger.info("Deleting all existing current employee records...")
        return self.current_employee_repo.truncate_table()
    
    def bulk_import_employees(self, rows: List[Dict[str, str]]) -> bool:
        """Import CSV data into current_employee table using batch processing"""
        record_count = len(rows)
        logger.info(f"Inserting {record_count} current employee records...")
        
        # Process in batches for better performance
        batch_size = 1000
        total_batches = (record_count + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, record_count)
            batch_rows = rows[start_idx:end_idx]
            
            with self.current_employee_repo.adapter:
                for row in batch_rows:
                    record = CurrentEmployee(
                        primary_branch=clean_string(row.get('Primary Branch')),
                        employee_id=clean_string(row.get('Employee ID')),
                        first_name=clean_string(row.get('First Name')),
                        last_name=clean_string(row.get('Last Name')),
                        suffix=clean_string(row.get('Suffix')),
                        employee_type=clean_string(row.get('Employee Type')),
                        user_type=clean_string(row.get('User Type')),
                        address_1=clean_string(row.get('Address 1')),
                        address_2=clean_string(row.get('Address 2')),
                        city=clean_string(row.get('City')),
                        state=clean_string(row.get('State')),
                        zip_code=clean_string(row.get('ZIP Code')),
                        email_address=clean_string(row.get('Email Address')),
                        phone_1=clean_string(row.get('Phone 1')),
                        phone_2=clean_string(row.get('Phone 2')),
                        payroll_start_date=clean_string(row.get('Payroll Start Date')),
                        hire_date=clean_string(row.get('Hire Date')),
                        date_of_birth=clean_string(row.get('Date of Birth'))
                    )
                    
                    self.current_employee_repo.insert_employee(record)
            
            logger.info(f"Completed batch {batch_num+1}/{total_batches}")
        
        logger.info("Successfully imported current employee data")
        return True


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
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        
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
