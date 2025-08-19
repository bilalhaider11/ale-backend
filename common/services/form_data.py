from typing import List, Optional
from datetime import datetime
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.form_data import FormData
from common.app_logger import get_logger

logger = get_logger(__name__)


class FormDataService:
    """
    Service class for handling form data operations.
    Provides business logic for form data management.
    """

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.form_data_repo = self.repository_factory.get_repository(RepoType.FORM_DATA)
        self.employee_repo = self.repository_factory.get_repository(RepoType.EMPLOYEE)
        self.person_repo = self.repository_factory.get_repository(RepoType.PERSON)

    def save_form_field(self, person_id: str, form_name: str, field_name: str, value: str, 
                       organization_id: str = None) -> FormData:
        """
        Save a new form field value.
        
        Args:
            person_id: The person's entity ID
            form_name: The name of the form
            field_name: The name of the field
            value: The field value
            organization_id: Organization ID for employee updates
            
        Returns:
            The saved FormData object
            
        Raises:
            ValueError: If validation fails or field already exists
        """
        logger.info(f"Saving new form field: person_id={person_id}, form={form_name}, field={field_name}")
        
        # Validate inputs
        if not all([person_id, form_name, field_name]):
            raise ValueError("person_id, form_name, and field_name are required")
        
        # Check if person exists in database
        self._validate_person_exists(person_id)
        
        # Convert value to string and handle None
        value = str(value) if value is not None else ""

        # Save the form field
        form_data = self.form_data_repo.save_form_field(
            person_id, form_name, field_name, value
        )

        # Check if this field should update employee data
        self._check_and_update_employee_data(person_id, form_name, field_name, value, organization_id)
        
        logger.info(f"Successfully saved new form field: {form_data.entity_id}")
        return form_data


    def get_form_data_by_person(self, person_id: str) -> List[FormData]:
        """
        Get all form data for a person.
        
        Args:
            person_id: The person's entity ID
            
        Returns:
            List of FormData objects
            
        Raises:
            ValueError: If the person doesn't exist
        """
        logger.info(f"Retrieving form data for person: {person_id}")
        
        # Check if person exists in database
        self._validate_person_exists(person_id)
        
        form_data = self.form_data_repo.get_form_data_by_person_id(person_id)
        
        logger.info(f"Retrieved {len(form_data)} form data records for person: {person_id}")
        return form_data

    def get_form_data_by_person_and_form(self, person_id: str, form_name: str) -> List[FormData]:
        """
        Get form data for a specific person and form.
        
        Args:
            person_id: The person's entity ID
            form_name: The name of the form
            
        Returns:
            List of FormData objects
            
        Raises:
            ValueError: If the person doesn't exist
        """
        logger.info(f"Retrieving form data for person: {person_id}, form: {form_name}")
        
        # Check if person exists in database
        self._validate_person_exists(person_id)
        
        form_data = self.form_data_repo.get_form_data_by_person_and_form(person_id, form_name)
        
        logger.info(f"Retrieved {len(form_data)} form data records for person: {person_id}, form: {form_name}")
        return form_data


    def _check_and_update_employee_data(self, person_id: str, form_name: str, field_name: str, 
                                       value: str, organization_id: str) -> None:
        """
        Check if form field contains employee-relevant data and update employee record if needed.
        
        Args:
            person_id: The person's entity ID
            form_name: The name of the form
            field_name: The name of the field
            value: The field value
            organization_id: Organization ID for employee lookup
        """
        try:
            # Define fields that should update employee data
            employee_update_fields = {
                'date_of_birth': 'date_of_birth',
                'dob': 'date_of_birth',
                'birth_date': 'date_of_birth',
                'hire_date': 'hire_date',
                'date_of_hire': 'hire_date',
                'employment_date': 'hire_date',
                'start_date': 'hire_date',
                'first_name': 'first_name',
                'last_name': 'last_name',
                'email': 'email_address',
                'email_address': 'email_address',
                'phone': 'phone_1',
                'phone_number': 'phone_1',
                'address': 'address_1',
                'street_address': 'address_1',
                'city': 'city',
                'state': 'state',
                'zip_code': 'zip_code',
                'postal_code': 'zip_code',
                'ssn': 'social_security_number',
                'social_security_number': 'social_security_number'
            }
            
            field_lower = field_name.lower()
            
            # Update Employee record if applicable
            if field_lower in employee_update_fields and organization_id:
                self._update_employee_field(person_id, organization_id, employee_update_fields[field_lower], value)
            
            # Update Person record for name fields
            if field_lower in ['first_name', 'last_name']:
                self._update_person_name(person_id, field_lower, value)
                
        except Exception as e:
            logger.warning(f"Failed to update employee data from form field: {e}")

    def _update_employee_field(self, person_id: str, organization_id: str, employee_field: str, value: str) -> None:
        """Update a specific employee field."""
        employee = self.employee_repo.get_one({'person_id': person_id, 'organization_id': organization_id})
        if employee:
            converted_value = self._convert_value_for_employee_field(employee_field, value)
            if converted_value is not None:
                setattr(employee, employee_field, converted_value)
                self.employee_repo.save(employee)
                logger.info(f"Updated employee {employee_field} from form data: {person_id}")

    def _convert_value_for_employee_field(self, employee_field: str, value: str) -> Optional[str]:
        """
        Convert form value to appropriate type for employee field.
        
        Args:
            employee_field: The employee field name
            value: The form field value
            
        Returns:
            Converted value or None if conversion fails
        """
        if not value or not value.strip():
            return None
        
        # Date fields
        if employee_field in ['date_of_birth', 'hire_date']:
            return self._parse_date_string(value)
        
        # String fields
        return str(value).strip()

    def _parse_date_string(self, date_string: str) -> Optional[str]:
        """
        Parse date string to YYYY-MM-DD format.
        
        Args:
            date_string: Date string in various formats
            
        Returns:
            Date string in YYYY-MM-DD format or None if invalid
        """
        if not date_string or not date_string.strip():
            return None
        
        # Common date formats to try
        date_formats = [
            '%Y-%m-%d',      # 2023-12-25
            '%m/%d/%Y',      # 12/25/2023
            '%m-%d-%Y',      # 12-25-2023
            '%d/%m/%Y',      # 25/12/2023
            '%d-%m-%Y',      # 25-12-2023
            '%Y/%m/%d',      # 2023/12/25
            '%m/%d/%y',      # 12/25/23
            '%m-%d-%y',      # 12-25-23
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_string.strip(), fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_string}")
        return None

    def _update_person_name(self, person_id: str, field_name: str, value: str) -> None:
        """
        Update the Person record with first_name or last_name.
        
        Args:
            person_id: The person's entity ID
            field_name: The field name ('first_name' or 'last_name')
            value: The field value
        """
        try:
            person = self.person_repo.get_one({'entity_id': person_id})
            if person:
                setattr(person, field_name, value)
                self.person_repo.save(person)
                logger.info(f"Updated person {field_name} from form data: {person_id}")
            else:
                logger.warning(f"Person not found for ID: {person_id}")
                
        except Exception as e:
            logger.warning(f"Failed to update person {field_name} from form field: {e}")

    def _validate_person_exists(self, person_id: str) -> None:
        """
        Validate that the person exists in the database.
        
        Args:
            person_id: The person's entity ID
            
        Raises:
            ValueError: If the person doesn't exist
        """
        try:
            from common.services.person import PersonService
            person_service = PersonService(self.config)
            
            person = person_service.get_person_by_id(person_id)
            if not person:
                raise ValueError(f"Person with ID '{person_id}' does not exist in the database")
                
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            logger.error(f"Error validating person existence for ID '{person_id}': {e}")
            raise ValueError(f"Unable to validate person existence for ID '{person_id}'")



