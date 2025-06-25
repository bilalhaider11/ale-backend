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
        self.employees_prefix = f"{config.AWS_S3_KEY_PREFIX}employees-list/"

    def delete_all_employees(self) -> bool:
        """Delete all existing current employee records"""
        logger.info("Deleting all existing current employee records...")
        return self.current_employee_repo.truncate_table()
    
    def bulk_import_employees(self, rows: List[Dict[str, str]], organization_id: str) -> bool:
        """Import CSV data into current_employee table using batch processing"""
        record_count = len(rows)
        logger.info(f"Processing {record_count} current employee records...")
        
        records = []
        for row in rows:
            employee_type = None

            if row.get('caregiver id'):
                employee_type = "caregiver"
            if row.get('employee id'):
                employee_type = "employee"

            if row.get('employee id') and row.get('caregiver id'):
                logger.warning(f"Row has both employee and caregiver ID, using employee ID.")

            if employee_type is None:
                logger.warning(f"Skipping row with neither employee nor caregiver ID: {row}")
                continue

            record = CurrentEmployee(
                primary_branch=clean_string(row.get('primary branch')),
                employee_id=clean_string(row.get('employee id')) or clean_string(row.get('caregiver id')),
                first_name=clean_string(row.get('first name')),
                last_name=clean_string(row.get('last name')),
                suffix=clean_string(row.get('suffix')),
                employee_type=clean_string(row.get('employee type')) or employee_type,
                user_type=clean_string(row.get('user type')),
                address_1=clean_string(row.get('address 1')) or clean_string(row.get('address')),
                address_2=clean_string(row.get('address 2')),
                city=clean_string(row.get('city')),
                state=clean_string(row.get('state')),
                zip_code=clean_string(row.get('zip code')) or clean_string(row.get('postal code')),
                email_address=clean_string(row.get('email address')) or clean_string(row.get('email')),
                phone_1=clean_string(row.get('phone 1')),
                phone_2=clean_string(row.get('phone 2')),
                payroll_start_date=clean_string(row.get('payroll start date')),
                hire_date=clean_string(row.get('hire date')),
                date_of_birth=clean_string(row.get('date of birth')),
                caregiver_tags=clean_string(row.get('caregiver tags')),
                organization_id=organization_id
            )

            records.append(record)

        self.current_employee_repo.upsert_employees(records, organization_id)
        logger.info("Successfully imported current employee data")


    def upload_employee_list(self, organization_id, file_path, original_filename=None):
        """
        Upload a CSV or XLSX file to S3 bucket under employees-list/ prefix.
        Creates a timestamped file: employees-list/<organization_id>/<timestamp>.<extension>
        
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
        timestamped_key = f"{self.employees_prefix}{organization_id}/{timestamp}{file_extension}"

        # Define S3 key for latest file
        latest_key = f"{self.employees_prefix}{organization_id}/latest"

        # Prepare metadata
        metadata = {
            "upload_date": timestamp,
            "organization_id": organization_id
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


    def get_last_uploaded_file_status(self, organization_id):
        s3_key = f"{self.employees_prefix}{organization_id}/latest"
        try:
            metadata = self.s3_client.get_object_metadata(s3_key)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            raise e

        upload_date = metadata.get('upload_date', None)
        original_filename = metadata.get('original_filename', None)
        file_size = metadata.get('ContentLength', 0)

        tags = self.s3_client.get_object_tags(s3_key)
        status = tags.get('status', 'unknown')
        error = tags.get('error', None)
        file_url = self.s3_client.generate_presigned_url(s3_key, filename=original_filename)

        current_employee_count = self.get_employees_count(organization_id=organization_id)

        return {
            "upload_date": upload_date,
            "filename": original_filename,
            "filesize": file_size,
            "status": status,
            "error": error,
            "count": current_employee_count,
            "file_url": file_url
        }

    def get_employee_by_id(self, employee_id: str) -> CurrentEmployee:
        """
        Retrieve a current employee record by employee ID.
        
        Args:
            employee_id (str): The unique identifier for the employee.
        
        Returns:
            CurrentEmployee: The employee record if found, otherwise None.
        """
        return self.current_employee_repo.get_by_employee_id(employee_id)

    def get_employees_count(self, organization_id=None) -> int:
        """
        Get the count of current employees in the database.
        
        Returns:
            int: The number of current employees.
        """
        return self.current_employee_repo.get_employees_count(organization_id=organization_id)
