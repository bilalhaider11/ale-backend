from dataclasses import dataclass
from typing import Optional

@dataclass(kw_only=True)
class CurrentCaregiver():
    """
    Represents a current caregiver from the CSV import.
    This is a non-versioned model that gets replaced on each import.
    """
    id: int = None
    caregiver_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    hire_date: Optional[str] = None
    caregiver_tags: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
