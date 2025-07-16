from typing import List, Dict
from datetime import datetime
import os
import uuid

from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.employee import Employee
from common.models.current_employees_file import CurrentEmployeesFile, CurrentEmployeesFileStatusEnum
from common.services.s3_client import S3ClientService
from common.services.current_employees_file import CurrentEmployeesFileService
from common.helpers.csv_utils import get_first_matching_column_value

logger = get_logger(__name__)


class EmployeeService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.employee_repo = self.repository_factory.get_repository(RepoType.EMPLOYEE, message_queue_name="")
        self.person_repo = self.repository_factory.get_repository(RepoType.PERSON, message_queue_name="")
        self.current_employees_file_service = CurrentEmployeesFileService(config)
        self.s3_client = S3ClientService()
        self.bucket_name = config.AWS_S3_BUCKET_NAME
        self.employees_prefix = f"{config.AWS_S3_KEY_PREFIX}employees-list/"

    def bulk_import_employees(self, rows: List[Dict[str, str]], organization_id: str, user_id: str) -> bool:
        """Import CSV data into employee table using batch processing"""
        record_count = len(rows)
        logger.info(f"Processing {record_count} employee records...")

        records = []
        for row in rows:
            employee_type = None

            if get_first_matching_column_value(row, ['caregiver id', 'caregiver_id']):
                employee_type = "caregiver"
            if get_first_matching_column_value(row, ['employee id', 'employee_id']):
                employee_type = "employee"

            if get_first_matching_column_value(row, ['employee id', 'employee_id']) and get_first_matching_column_value(row, ['caregiver id', 'caregiver_id']):
                logger.warning(f"Row has both employee and caregiver ID, using employee ID.")

            if employee_type is None:
                logger.warning(f"Skipping row with neither employee nor caregiver ID: {row}")
                continue

            record = Employee(
                changed_by_id=user_id,
                primary_branch=get_first_matching_column_value(row, ['primary branch', 'primary_branch']),
                employee_id=get_first_matching_column_value(row, ['employee id', 'employee_id', 'caregiver id', 'caregiver_id']),
                first_name=get_first_matching_column_value(row, ['first name', 'first_name']),
                last_name=get_first_matching_column_value(row, ['last name', 'last_name']),
                suffix=get_first_matching_column_value(row, ['suffix']),
                employee_type=get_first_matching_column_value(row, ['employee type', 'employee_type']) or employee_type,
                user_type=get_first_matching_column_value(row, ['user type', 'user_type']),
                address_1=get_first_matching_column_value(row, ['address 1', 'address_1', 'address']),
                address_2=get_first_matching_column_value(row, ['address 2', 'address_2']),
                city=get_first_matching_column_value(row, ['city']),
                state=get_first_matching_column_value(row, ['state']),
                zip_code=get_first_matching_column_value(row, ['zip code', 'postal code']),
                email_address=get_first_matching_column_value(row, ['email address', 'email']),
                phone_1=get_first_matching_column_value(row, ['phone 1', 'phone']),
                phone_2=get_first_matching_column_value(row, ['phone 2']),
                payroll_start_date=get_first_matching_column_value(row, ['payroll start date']),
                hire_date=get_first_matching_column_value(row, ['hire date']),
                date_of_birth=get_first_matching_column_value(row, ['date of birth']),
                caregiver_tags=get_first_matching_column_value(row, ['caregiver tags', 'tags']),
                social_security_number=get_first_matching_column_value(row, ['social security number', 'ssn'], match_mode='contains'),
                organization_id=organization_id
            )

            records.append(record)

        count = len(records)
        self.employee_repo.upsert_employees(records, organization_id)

        logger.info(f"Successfully imported {count} employee data")
        return count


    def upload_employee_list(self, organization_id, person_id, file_path, file_id=None, original_filename=None):
        """
        Upload a CSV or XLSX file to S3 bucket under employees-list/ prefix.
        Creates a timestamped file: employees-list/<organization_id>/<timestamp>.<extension>
        
        Args:
            file_path (str): Local path to the CSV or XLSX file
            original_filename (str): Original filename to store in metadata
        
        Returns:
            dict: Information about the uploaded file including key and URL
        """
        logger.info(f"Uploading employee list file: {file_path} for organization: {organization_id}")

        if file_id is None:
            file_id = uuid.uuid4().hex

        # Generate timestamp for file naming
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        
        # Determine file extension and file type
        file_extension = '.xlsx' if file_path.lower().endswith('.xlsx') else '.csv'
        file_type = 'xlsx' if file_path.lower().endswith('.xlsx') else 'csv'
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if file_type == 'xlsx' else 'text/csv'
        
        # Define S3 key for timestamped file
        file_id_key = f"{self.employees_prefix}{organization_id}/{file_id}"

        # Prepare metadata
        metadata = {
            "upload_date": timestamp,
            "organization_id": organization_id
        }

        if original_filename:
            metadata["original_filename"] = original_filename
        
        # Get file size
        file_size = os.path.getsize(file_path)

        # Create CurrentEmployeesFile instance
        current_employees_file = CurrentEmployeesFile(
            entity_id=file_id,
            organization_id=organization_id,
            file_name=original_filename or f"{timestamp}{file_extension}",
            file_size=file_size,
            file_type=file_type,
            s3_key=file_id_key,
            uploaded_at=datetime.now(),
            uploaded_by=person_id,
            status=CurrentEmployeesFileStatusEnum.PENDING
        )

        # Save file metadata to database
        saved_file = self.current_employees_file_service.save_employees_file(current_employees_file)

        # Upload the file with timestamp name
        self.s3_client.upload_file(
            file_path=file_path,
            s3_key=file_id_key,
            metadata=metadata,
            content_type=content_type
        )

        result = {
            "file": {
                "url": self.s3_client.generate_presigned_url(file_id_key, filename=original_filename or f"{timestamp}{file_extension}"),
            },
            "file_metadata": saved_file
        }

        return result


    def get_employee_by_id(self, employee_id: str, organization_id: str) -> Employee:
        """
        Retrieve an employee record by employee ID.
        
        Args:
            employee_id (str): The unique identifier for the employee.
            organization_id (str): The ID of the organization to filter by.
        
        Returns:
            Employee: The employee record if found, otherwise None.
        """
        return self.employee_repo.get_one({
            'entity_id': employee_id,
            'organization_id': organization_id
        })

    def get_employees_count(self, organization_id=None) -> int:
        """
        Get the count of employees in the database.

        Returns:
            int: The number of employees.
        """
        return self.employee_repo.get_employees_count(organization_id=organization_id)

    def reset_last_uploaded_file_status(self, organization_id: str):
        """
        Reset the status of the latest uploaded file to empty.
        
        Args:
            organization_id (str): The ID of the organization.
        """
        s3_key = f"{self.employees_prefix}{organization_id}/latest"
        self.s3_client.delete_object(s3_key)
        return True


    def get_employees_with_matches(self, organization_id: str) -> List[Employee]:
        """
        Get employees who have at least one match in the employee_exclusion_match table.
        
        Args:
            organization_id (str): The ID of the organization to filter by.
        
        Returns:
            List[Employee]: List of Employee objects with matches.
        """
        return self.employee_repo.get_employees_with_matches(organization_id)

    def get_employees_by_organization(self, organization_id: str) -> List[Employee]:
        """
        Get all employees belonging to a specific organization.

        Args:
            organization_id (str): The ID of the organization to filter by.

        Returns:
            List[Employee]: List of Employee objects belonging to the organization.
        """
        return self.employee_repo.get_employees_with_invitation_status(organization_id)
    
    def get_employee_by_person_id(self, person_id: str, organization_id: str) -> Employee:
        """
        Get employee for a specific person.

        Args:
            person_id (str): The ID of the person to filter by.

        Returns:
            Employee: The Employee object belonging to the person.
        """
        return self.employee_repo.get_one({'person_id': person_id, 'organization_id': organization_id})

    def save_employee(self, employee: Employee) -> Employee:
        """
        Save an employee record to the database.
        
        Args:
            employee (Employee): The employee object to save.
        
        Returns:
            Employee: The saved employee object with updated entity_id.
        """
        return self.employee_repo.save(employee)
