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

    @staticmethod
    def _iso(value):
        """ISO‑encode date / datetime / time objects."""
        if isinstance(value, (date, datetime, time)):
            return value.isoformat()
        return value

    @staticmethod
    def _identity(value):
        return value

    def as_dict(self, *, convert_datetime_to_iso_string=True, **_ignored):
        """
        Return JSON/DB‑ready dict.

        convert_datetime_to_iso_string can be:
        • True  → use Patient._iso
        • False → leave date/time objects untouched
        • callable → use the supplied converter
        """
        if callable(convert_datetime_to_iso_string):
            iso = convert_datetime_to_iso_string
        elif convert_datetime_to_iso_string:
            iso = self.__class__._iso          # ← always present now
        else:
            iso = self.__class__._identity

        result = {
            f.name: iso(getattr(self, f.name))
            for f in self.__dataclass_fields__.values()
            if not f.name.startswith('_')          # skip private flags
            and getattr(self, f.name) is not None
        }

        # names added by joins
        if hasattr(self, "first_name"):
            result["first_name"] = self.first_name
        if hasattr(self, "last_name"):
            result["last_name"] = self.last_name
        return result