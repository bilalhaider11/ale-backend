from dataclasses import dataclass
from datetime import time, date
from typing import ClassVar, Optional
from rococo.models import VersionedModel

@dataclass
class PatientCareSlot(VersionedModel):
    use_type_checking: ClassVar[bool] = True

    patient_id: str
    day_of_week: int
    start_time: time
    end_time: time
    week_start_date: date = None
    week_end_date: date = None
    is_consistent_slot: bool = True

