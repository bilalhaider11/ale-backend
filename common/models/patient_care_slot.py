from dataclasses import dataclass
from datetime import time, date
from typing import ClassVar, Optional
from rococo.models import VersionedModel


@dataclass
class PatientCareSlot(VersionedModel):
    use_type_checking: ClassVar[bool] = True

    patient_id: str = None
    series_id: Optional[str] = None
    day_of_week: int = None
    start_day_of_week: int = None
    end_day_of_week: int = None
    start_time: time = None
    end_time: time = None
    week_start_date: date = None
    week_end_date: date = None
    logical_key: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    def validate_logical_key(self):
        # Ensure logical key is set and consistent.
        self.logical_key = self.generate_logical_key(
            patient_id=self.patient_id,
            series_id=self.series_id,
            day_of_week=self.day_of_week,
            start_day_of_week=self.start_day_of_week,
            end_day_of_week=self.end_day_of_week,
            start_time=self.start_time,
            end_time=self.end_time,
            start_date=self.start_date
        )

    @classmethod
    def generate_logical_key(
        cls,
        patient_id: str,
        series_id: Optional[str] = None,
        day_of_week: int = None,
        start_day_of_week: int = None,
        end_day_of_week: int = None,
        start_time: time = None,
        end_time: time = None,
        start_date: Optional[date] = None
    ) -> str:
        """Generates a logical key for the patient care slot."""
        # Start with patient_id
        key_parts = [patient_id]

        # Add series_id if provided
        if series_id:
            key_parts.append(series_id)

        # Use day range if both start and end day are provided, otherwise use single day
        if start_day_of_week is not None and end_day_of_week is not None:
            day_part = f"{start_day_of_week}-{end_day_of_week}"
        else:
            day_part = str(day_of_week)
        key_parts.append(day_part)

        # Include time information if provided
        if start_time and end_time:
            key_parts.append(start_time.strftime('%H:%M:%S'))
            key_parts.append(end_time.strftime('%H:%M:%S'))

        # Add start_date at the end if provided
        if start_date:
            key_parts.append(start_date.strftime('%Y-%m-%d'))

        return "-".join(key_parts)