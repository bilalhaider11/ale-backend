from rococo.models import VersionedModel
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date, datetime

from datetime import date, datetime, time

@dataclass
class Patient(VersionedModel):
    person_id: Optional[str] = None               
    organization_id: str = None
    date_of_birth: date = None
    social_security_number: str = None
    care_period_start: date = None
    care_period_end: date = None
    weekly_quota: int = None
    current_week_remaining_quota: int = None  