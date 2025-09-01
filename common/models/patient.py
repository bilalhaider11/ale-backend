from rococo.models import VersionedModel
from dataclasses import dataclass
from typing import Optional
from datetime import date

@dataclass
class Patient(VersionedModel):
    person_id: Optional[str] = None               
    organization_id: str = None
    medical_record_number: str = None
    care_period_start: date = None
    care_period_end: date = None
    weekly_quota: int = None
    current_week_remaining_quota: int = None  