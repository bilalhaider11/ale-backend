from dataclasses import dataclass
from typing import Optional

@dataclass(kw_only=True)
class CurrentEmployee():
    """
    Represents a current employee from the CSV import.
    This is a non-versioned model that gets replaced on each import.
    """
    id: int = None
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
