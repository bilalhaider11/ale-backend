import uuid
from typing import Optional, Any
from datetime import time, timedelta, datetime, date
from common.models.patient_care_slot import PatientCareSlot
from common.models.availability_slot import AvailabilitySlot
from common.helpers.exceptions import InputValidationError

# Validation constants
MIN_DAY_OF_WEEK = 0
MAX_DAY_OF_WEEK = 6


def validate_and_parse_day_of_week(value: Any, field_name: str = "day_of_week", allow_none: bool = False) -> Optional[int]:
    """Validate and return day of week value."""
    if value is None:
        if allow_none:
            return None
        raise InputValidationError(f"{field_name} is required")
    
    if not isinstance(value, int) or not (MIN_DAY_OF_WEEK <= value <= MAX_DAY_OF_WEEK):
        raise InputValidationError(
            f"{field_name} must be an integer between {MIN_DAY_OF_WEEK} and {MAX_DAY_OF_WEEK}"
        )
    return value


def parse_time_field(value: Any, field_name: str) -> time:
    """Parse time from string or time object."""
    if isinstance(value, str):
        try:
            return datetime.strptime(value, '%H:%M').time()
        except ValueError:
            raise InputValidationError(f"{field_name} must be in 'HH:MM' format")
    elif isinstance(value, time):
        return value
    else:
        raise InputValidationError(f"{field_name} must be a time string in 'HH:MM' format or a time object")


def parse_date_field(value: Any, field_name: str, allow_none: bool = True) -> Optional[date]:
    """Parse date from string or date object."""
    if value is None:
        if not allow_none:
            today = datetime.now().date()
            return today - timedelta(days=today.weekday())
        return None
    
    if isinstance(value, str):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise InputValidationError(f"{field_name} must be in 'YYYY-MM-DD' format")
    elif isinstance(value, date):
        return value
    else:
        raise InputValidationError(f"{field_name} must be a date string in 'YYYY-MM-DD' format or a date object")



def validate_day_range(start_day: Optional[int], end_day: Optional[int]) -> None:
    """Validate that day range is valid."""
    if start_day is not None and end_day is not None:
        if start_day > end_day and not (start_day == 6 and end_day == 0):
            raise InputValidationError("start_day_of_week cannot be greater than end_day_of_week")


def is_valid_time_range(start_time: time, end_time: time) -> bool:
    """
    Validate if a time range is valid, including overnight slots.

    Args:
        start_time: Start time of the slot
        end_time: End time of the slot

    Returns:
        True if the time range is valid, False otherwise
    """
    if not start_time or not end_time:
        return False

    # Convert times to minutes for easier comparison
    start_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute

    # Handle overnight slots (e.g., 23:00 to 03:00)
    if start_minutes > end_minutes:
        # Calculate duration for overnight slots
        duration_minutes = (24 * 60 - start_minutes) + end_minutes
        # Allow any overnight slot with positive duration
        return duration_minutes > 0
    else:
        # Regular same-day slot - start must be before end
        return start_minutes < end_minutes


def expand_slots(payload: dict, start_date: str, entity_id: str, entity_type: str = "patient"):
    """
    Expand recurring slots for either patients or employees.

    Args:
        payload: Configuration dict with duration_weeks, selected_days, and shifts
        start_date: Start date for the series
        entity_id: Either patient_id or employee_id depending on entity_type
        entity_type: Either "patient" or "employee" (default: "patient")

    Returns:
        List of PatientCareSlot or AvailabilitySlot objects
    """
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date).date()
    elif isinstance(start_date, datetime):
        start_date = start_date.date()

    slots = []
    start_weekday = start_date.weekday()

    for week in range(payload["duration_weeks"]):
        for start_day_of_week in payload["selected_days"]:
            days_ahead = (start_day_of_week - start_weekday) % 7
            days_ahead += (week * 7)

            slot_date = start_date + timedelta(days=days_ahead)

            for shift in payload["shifts"]:
                sh, sm = map(int, shift["start_time"].split(":"))
                eh, em = map(int, shift["end_time"].split(":"))
                start_t = time(sh, sm)
                end_t = time(eh, em)

                is_overnight = end_t <= start_t

                if is_overnight:
                    slot_end_date = slot_date + timedelta(days=1)
                    end_dow = (start_day_of_week + 1) % 7
                else:
                    slot_end_date = slot_date
                    end_dow = start_day_of_week

                slots.append({
                    'entity_id': entity_id,
                    'start_day_of_week': start_day_of_week,
                    'end_day_of_week': end_dow,
                    'start_time': start_t,
                    'end_time': end_t,
                    'start_date': slot_date,
                    'end_date': slot_end_date
                })

    # Only assign series_id if there's more than one slot
    series_id = uuid.uuid4().hex if len(slots) > 1 else None

    # Convert dicts to actual slot objects
    result = []
    for slot_data in slots:
        if entity_type == "employee":
            result.append(
                AvailabilitySlot(
                    employee_id=slot_data['entity_id'],
                    series_id=series_id,
                    start_day_of_week=slot_data['start_day_of_week'],
                    end_day_of_week=slot_data['end_day_of_week'],
                    start_time=slot_data['start_time'],
                    end_time=slot_data['end_time'],
                    start_date=slot_data['start_date'],
                    end_date=slot_data['end_date']
                )
            )
        else:  # patient
            result.append(
                PatientCareSlot(
                    patient_id=slot_data['entity_id'],
                    series_id=series_id,
                    start_day_of_week=slot_data['start_day_of_week'],
                    end_day_of_week=slot_data['end_day_of_week'],
                    start_time=slot_data['start_time'],
                    end_time=slot_data['end_time'],
                    start_date=slot_data['start_date'],
                    end_date=slot_data['end_date']
                )
            )

    return result

def get_week_start_date(date_:date):
   
    # Get the weekday as an integer (Monday=0, Sunday=6)
    day_of_week = date_.weekday()

    # Calculate the number of days to subtract to reach Monday
    # If it's already Monday (0), subtract 0 days
    # If it's Tuesday (1), subtract 1 day, and so on.
    days_to_subtract = day_of_week

    # Subtract the calculated days from the original date
    start_of_week = date_ - timedelta(days=days_to_subtract)
    return start_of_week