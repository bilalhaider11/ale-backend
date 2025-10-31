from dataclasses import dataclass
from datetime import time, date
from typing import ClassVar, Optional
from rococo.models import VersionedModel


@dataclass
class AvailabilitySlot(VersionedModel):
    use_type_checking: ClassVar[bool] = True

    start_day_of_week: int = None
    end_day_of_week: int = None
    start_time: time = None
    end_time: time = None
    employee_id: str = None
    series_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    def validate_start_day_of_week(self):
        if not isinstance(self.start_day_of_week, int) or self.start_day_of_week < 0 or self.start_day_of_week > 6:
            self.start_day_of_week = 0

   