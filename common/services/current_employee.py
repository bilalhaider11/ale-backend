from typing import List, Dict
from datetime import datetime
import botocore.exceptions

from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.current_employee import CurrentEmployee
from common.services.s3_client import S3ClientService
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
                        primary_branch=clean_string(row.get('primary branch')),
                        employee_id=clean_string(row.get('employee id')),
                        first_name=clean_string(row.get('first name')),
                        last_name=clean_string(row.get('last name')),
                        suffix=clean_string(row.get('suffix')),
                        employee_type=clean_string(row.get('employee type')),
                        user_type=clean_string(row.get('user type')),
                        address_1=clean_string(row.get('address 1')),
                        address_2=clean_string(row.get('address 2')),
                        city=clean_string(row.get('city')),
                        state=clean_string(row.get('state')),
                        zip_code=clean_string(row.get('zip code')),
                        email_address=clean_string(row.get('email address')),
                        phone_1=clean_string(row.get('phone 1')),
                        phone_2=clean_string(row.get('phone 2')),
                        payroll_start_date=clean_string(row.get('payroll start date')),
                        hire_date=clean_string(row.get('hire date')),
                        date_of_birth=clean_string(row.get('date of birth'))
                    )
                    
                    self.current_employee_repo.insert_employee(record)
            
            logger.info(f"Completed batch {batch_num+1}/{total_batches}")
        
        logger.info("Successfully imported current employee data")


    def upload_employee_list(self, file_path, original_filename=None):
        """
        Upload a CSV or XLSX file to S3 bucket under employees-list/ prefix.
        Creates a timestamped file: employees-list/<timestamp>.<extension>
        
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
        timestamped_key = f"{self.employees_prefix}{timestamp}{file_extension}"

        # Define S3 key for latest file
        latest_key = f"{self.employees_prefix}latest"

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


    def get_last_uploaded_file_status(self):
        s3_key = f"{self.employees_prefix}latest"
        try:
            metadata = self.s3_client.get_object_metadata(s3_key)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            raise e

        upload_date = metadata.get('upload_date', None)
        original_filename = metadata.get('original_filename', None)

        tags = self.s3_client.get_object_tags(s3_key)
        status = tags.get('status', 'unknown')
        error = tags.get('error', None)
        file_url = self.s3_client.generate_presigned_url(s3_key, filename=original_filename)

        return {
            "upload_date": upload_date,
            "filename": original_filename,
            "status": status,
            "error": error,
            "file_url": file_url
        }
