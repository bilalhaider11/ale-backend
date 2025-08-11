from dataclasses import dataclass
from datetime import time, date
from typing import ClassVar, Optional
from rococo.models import VersionedModel

@dataclass
class PatientCareSlot(VersionedModel):
    use_type_checking: ClassVar[bool] = True

    patient_id: str = None
    day_of_week: int = None
    start_time: time = None
    end_time: time = None
    week_start_date: date = None
    week_end_date: date = None
    is_consistent_slot: bool = True
    logical_key: str = ""

    def validate_logical_key(self):
        # Ensure logical key is set and consistent.
        self.logical_key = self.generate_logical_key(
            patient_id=self.patient_id,
            day_of_week=self.day_of_week,
            start_time=self.start_time,
            end_time=self.end_time
        )

    @classmethod
    def generate_logical_key(cls, patient_id: str, day_of_week: int, start_time: time, end_time: time) -> str:
        """Generates a logical key for the patient care slot."""
        return f"{patient_id}-{day_of_week}-{start_time.strftime('%H:%M:%S')}-{end_time.strftime('%H:%M:%S')}"
