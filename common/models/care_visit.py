from dataclasses import dataclass
from datetime import datetime
from typing import Optional, ClassVar
from enum import StrEnum
from rococo.models import VersionedModel


class CareVisitStatusEnum(StrEnum):
    SCHEDULED = "scheduled"
    CLOCKED_IN = "clocked_in"
    CLOCKED_OUT = "clocked_out"
    CANCELLED = "cancelled"
    MISSED = "missed"
    COMPLETED = "completed"

    def __repr__(self):
        return str(self.value)

    @classmethod
    def values(cls):
        return [v.value for v in cls.__members__.values() if isinstance(v, cls)]


@dataclass
class CareVisit(VersionedModel):
    use_type_checking: ClassVar[bool] = True

    status: CareVisitStatusEnum = CareVisitStatusEnum.SCHEDULED
    patient_id: str = ""
    employee_id: str = ""
    visit_date: Optional[datetime] = None
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    clock_in_time: Optional[datetime] = None
    clock_out_time: Optional[datetime] = None
    scheduled_by_id: str = ""
    availability_slot_key: str = ""
    patient_care_slot_key: str = ""
    organization_id: str = ""
