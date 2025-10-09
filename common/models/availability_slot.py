from dataclasses import dataclass
from datetime import time, date
from typing import ClassVar, Optional
from rococo.models import VersionedModel


@dataclass
class AvailabilitySlot(VersionedModel):
    use_type_checking: ClassVar[bool] = True

    day_of_week: int = None
    start_day_of_week: int = None
    end_day_of_week: int = None
    start_time: time = None
    end_time: time = None
    employee_id: str = None
    series_id: Optional[str] = None
    week_start_date: date = None
    week_end_date: date = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    def validate_day_of_week(self):
        if not isinstance(self.day_of_week, int) or self.day_of_week < 0 or self.day_of_week > 6:
            self.day_of_week = 0