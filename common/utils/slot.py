import uuid
from datetime import time, timedelta, datetime
from common.models.patient_care_slot import PatientCareSlot
from common.models.availability_slot import AvailabilitySlot


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
        for day_of_week in payload["selected_days"]:
            days_ahead = (day_of_week - start_weekday) % 7
            days_ahead += (week * 7)

            slot_date = start_date + timedelta(days=days_ahead)

            # Calculate week_start and week_end (needed for patient slots)
            week_start = slot_date - timedelta(days=slot_date.weekday())
            week_end = week_start + timedelta(days=6)

            for shift in payload["shifts"]:
                sh, sm = map(int, shift["start_time"].split(":"))
                eh, em = map(int, shift["end_time"].split(":"))
                start_t = time(sh, sm)
                end_t = time(eh, em)

                is_overnight = end_t <= start_t

                if is_overnight:
                    slot_end_date = slot_date + timedelta(days=1)
                    end_dow = (day_of_week + 1) % 7
                else:
                    slot_end_date = slot_date
                    end_dow = day_of_week

                slots.append({
                    'entity_id': entity_id,
                    'day_of_week': day_of_week,
                    'start_day_of_week': day_of_week,
                    'end_day_of_week': end_dow,
                    'week_start_date': week_start,
                    'week_end_date': week_end,
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
                    day_of_week=slot_data['day_of_week'],
                    start_day_of_week=slot_data['start_day_of_week'],
                    end_day_of_week=slot_data['end_day_of_week'],
                    week_start_date=slot_data['week_start_date'],
                    week_end_date=slot_data['week_end_date'],
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
                    day_of_week=slot_data['day_of_week'],
                    start_day_of_week=slot_data['start_day_of_week'],
                    end_day_of_week=slot_data['end_day_of_week'],
                    start_time=slot_data['start_time'],
                    end_time=slot_data['end_time'],
                    week_start_date=slot_data['week_start_date'],
                    week_end_date=slot_data['week_end_date'],
                    start_date=slot_data['start_date'],
                    end_date=slot_data['end_date']
                )
            )

    return result
