from typing import List, Dict, Any
from datetime import datetime
import os
import uuid
from common.models.alert import AlertLevelEnum, AlertStatusEnum

from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.employee import Employee
from common.models.current_employees_file import CurrentEmployeesFile, CurrentEmployeesFileStatusEnum
from common.services.s3_client import S3ClientService
from common.services.alert import AlertService
from common.services.current_employees_file import CurrentEmployeesFileService
from common.helpers.csv_utils import get_first_matching_column_value,is_valid_email
from common.tasks.send_message import send_message

logger = get_logger(__name__)

class EmployeeService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.employee_repo = self.repository_factory.get_repository(RepoType.EMPLOYEE, message_queue_name="")
        self.person_repo = self.repository_factory.get_repository(RepoType.PERSON, message_queue_name="")
        self.current_employees_file_service = CurrentEmployeesFileService(config)
        self.s3_client = S3ClientService()
        self.alert_service = AlertService(config)
        self.bucket_name = config.AWS_S3_BUCKET_NAME
        self.employees_prefix = f"{config.AWS_S3_KEY_PREFIX}employees-list/"
        self.physicians_prefix = f"{config.AWS_S3_KEY_PREFIX}physicians-list/"

    def bulk_import_employees(self, rows: List[Dict[str, str]], organization_id: str, user_id: str) -> tuple[int, list[dict[str, Any]]]:
        
        """Import CSV data into employee table using batch processing"""
        record_count = len(rows)
        logger.info(f"Processing {record_count} employee records...")
    
        from common.services.organization import OrganizationService
        from common.services import PersonService, AlertService
        from common.models import AlertLevelEnum, AlertStatusEnum
        from common.app_config import config
    
        organization_service = OrganizationService(self.config)
        alert_service = AlertService(config)
    
        def safe_parse_date(date_string: str):
            if not date_string or not date_string.strip():
                return None
            import dateparser
            try:
                dt = dateparser.parse(date_string, settings={
                    'DATE_ORDER': 'MDY',
                    'PREFER_DAY_OF_MONTH': 'first',
                    'PREFER_DATES_FROM': 'past',
                    'STRICT_PARSING': True
                })
                return dt.date().isoformat() if dt else None
            except Exception:
                return None
    
        skipped_entries = []
        success_count = 0
    
        # Fetch all existing employee IDs for the organization ONCE
        existing_employee_ids = self.employee_repo.get_employee_ids_map_for_organization(organization_id)
            
        for row in rows:
            first_name = get_first_matching_column_value(row, ['first name', 'first_name'])
            last_name = get_first_matching_column_value(row, ['last name', 'last_name'])
            email_address = get_first_matching_column_value(row,['email address','email_address','email','email-address'])
    
            if not first_name or not last_name or not email_address:
                skipped_entries.append(row)
                continue
            
            validate_email = is_valid_email(email_address)
            if validate_email == False :
                skipped_entries.append(row)
                continue
            
            # Create Employee record
            
            record = Employee(
                changed_by_id=user_id,
                primary_branch=get_first_matching_column_value(row, ['primary branch', 'primary_branch']),
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                suffix=get_first_matching_column_value(row, ['suffix']),
                employee_type=get_first_matching_column_value(row, ['employee type', 'employee_type']) or "employee",
                user_type=get_first_matching_column_value(row, ['user type', 'user_type']),
                address_1=get_first_matching_column_value(row, ['address 1', 'address_1', 'address']),
                address_2=get_first_matching_column_value(row, ['address 2', 'address_2']),
                city=get_first_matching_column_value(row, ['city']),
                state=get_first_matching_column_value(row, ['state']),
                zip_code=get_first_matching_column_value(row, ['zip code', 'postal code','zip_code','postal_code']),
                email_address=get_first_matching_column_value(row, ['email_address','email address', 'email']),
                phone_1=get_first_matching_column_value(row, ['phone1', 'phone']),
                phone_2=get_first_matching_column_value(row, ['phone2']),
                payroll_start_date=parsed_payroll_start_date,
                hire_date=parsed_hire_date,
                date_of_birth=parsed_date_of_birth,
                caregiver_tags=get_first_matching_column_value(row, ['caregiver tags', 'tags']),
                social_security_number=get_first_matching_column_value(row, ['social security number', 'ssn'], match_mode='contains'),
                organization_id=organization_id
            )
            # Get employee_id or auto-generate
            employee_id = get_first_matching_column_value(row, ['employee id', 'employee_id', 'caregiver id', 'caregiver_id'])
            if not employee_id or not employee_id.strip():
                employee_id = organization_service.get_next_employee_id(organization_id)
    
            # Detect duplicates in DB
            if employee_id in existing_employee_ids:
                existing_employee = existing_employee_ids[employee_id]
                logger.warning(
                    f"Duplicate employee ID detected during bulk import: {employee_id} on Entity-ID: {record.entity_id}"
                    f"employee to be created: {record.first_name} {record.last_name}"
                    f"for organization {organization_id}. Existing employee: "
                    f"{existing_employee.first_name} {existing_employee.last_name}"
                )
                # Create an alert
                alert_service.create_alert(
                    organization_id=organization_id,
                    title="Duplicate Employee ID Detected",
                    description=(
                        f"Duplicate employee ID: {record.employee_id} detected during bulk import. "
                        f"Existing employee: {existing_employee.entity_id} "
                        f"({existing_employee.first_name} {existing_employee.last_name}). "
                        f"Imported employee: {record.first_name} {record.last_name}."
                    ),
                    alert_type=AlertLevelEnum.WARNING.value,
                    status=AlertStatusEnum.ADDRESSED.value,
                )
            # Parse date fields
            parsed_hire_date = safe_parse_date(get_first_matching_column_value(row, ['hire date']))
            parsed_payroll_start_date = safe_parse_date(get_first_matching_column_value(row, ['payroll start date']))
            parsed_date_of_birth = safe_parse_date(get_first_matching_column_value(row, ['date_of_birth']))
    
            # Upsert single employee
            self.employee_repo.upsert_employee(record, organization_id)
            success_count += 1
    
        return success_count, skipped_entries

    def upload_list_file(self, organization_id, person_id, file_path, file_category, file_id=None, original_filename=None):
        """
        Upload a CSV or XLSX file to S3 bucket under the appropriate prefix based on file category.
        Creates a timestamped file in the appropriate S3 location.
        
        Args:
            organization_id (str): The ID of the organization
            person_id (str): The ID of the person uploading the file
            file_path (str): Local path to the CSV or XLSX file
            file_category (str): Type of file - "employee" or "physician"
            file_id (str, optional): ID to use for the file, if None a new UUID will be generated
            original_filename (str, optional): Original filename to store in metadata
        
        Returns:
            dict: Information about the uploaded file including key and URL
        """
        # Determine which prefix to use based on file category
        s3_prefix = self.employees_prefix
        if file_category == "physician":
            s3_prefix = self.physicians_prefix
        
        logger.info(f"Uploading {file_category} list file: {file_path} for organization: {organization_id}")

        if file_id is None:
            file_id = uuid.uuid4().hex

        # Generate timestamp for file naming
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        
        # Determine file extension and file type
        file_extension = '.xlsx' if file_path.lower().endswith('.xlsx') else '.csv'
        file_type = 'xlsx' if file_path.lower().endswith('.xlsx') else 'csv'
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if file_type == 'xlsx' else 'text/csv'
        
        # Define S3 key for timestamped file
        file_id_key = f"{s3_prefix}{organization_id}/{file_id}"
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
            status=CurrentEmployeesFileStatusEnum.PENDING,
            file_category=file_category
        )
        # Save file metadata to database
        saved_file = self.current_employees_file_service.save_employees_file (current_employees_file)
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

    def get_employee_by_id(self, entity_id: str, organization_id: str) -> Employee:
        """
        Retrieve an employee record by employee ID.
        
        Args:
            entity_id (str): The unique identifier for the employee.
            organization_id (str): The ID of the organization to filter by.
        
        Returns:
            Employee: The employee record if found, otherwise None.
        """
        return self.employee_repo.get_one({
            'entity_id': entity_id,
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

    def get_employees_by_organization(self, organization_ids: List[str], employee_type: str = None) -> List[Employee]:
        """
        Get all employees belonging to a specific organization.

        Args:
            organization_ids (List[str]): The IDs of the organizations to filter by.
            employee_type (str, optional): Filter by employee type (e.g., 'employee', 'caregiver', 'physician').

        Returns:
            List[Employee]: List of Employee objects belonging to the organization.
        """
        return self.employee_repo.get_employees_with_invitation_status(organization_ids, employee_type=employee_type)

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

    def trigger_match_for_employee(self, entity_id: str):
        logger.info("Triggering matching process for employee: %s", entity_id)
        logger.info("Sending message to queue: %s",
            self.config.PREFIXED_EMPLOYEE_EXCLUSION_MATCH_PROCESSOR_QUEUE_NAME
        )
        send_message(
            queue_name=self.config.PREFIXED_EMPLOYEE_EXCLUSION_MATCH_PROCESSOR_QUEUE_NAME,
            data={
                'action': 'match_exclusions',
                'source': 'employee_creation',
                'employee_id': entity_id
            }
        )