from dataclasses import dataclass
from typing import Optional, ClassVar
from rococo.models import VersionedModel

@dataclass
class Employee(VersionedModel):
    use_type_checking: ClassVar[bool] = True
    """
    Represents a current employee from the CSV import.
    This is a versioned model that tracks employee data over time.
    """
    primary_branch: Optional[str] = None
    employee_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    suffix: Optional[str] = None
    employee_type: Optional[str] = None
    user_type: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    email_address: Optional[str] = None
    phone_1: Optional[str] = None
    phone_2: Optional[str] = None
    payroll_start_date: Optional[str] = None
    hire_date: Optional[str] = None
    date_of_birth: Optional[str] = None
    organization_id: Optional[str] = None
    caregiver_tags: Optional[str] = None
    social_security_number: Optional[str] = None
    person_id: Optional[str] = None


    def validate_date_of_birth(self):
        """
        If date_of_birth is empty, it sets it to None.
        """
        if not self.date_of_birth:
            self.date_of_birth = None
