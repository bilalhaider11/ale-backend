from dataclasses import dataclass
from datetime import time
from typing import ClassVar
from rococo.models import VersionedModel


@dataclass
class AvailabilitySlot(VersionedModel):
    use_type_checking: ClassVar[bool] = True

    day_of_week: int = None
    start_time: time = None
    end_time: time = None
    employee_id: str = None

    def validate_day_of_week(self):
        if not isinstance(self.day_of_week, int) or self.day_of_week < 0 or self.day_of_week > 6:
            self.day_of_week = 0
