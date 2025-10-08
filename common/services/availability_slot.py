from typing import List, Optional
from common.helpers.exceptions import NotFoundError, InputValidationError
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.availability_slot import AvailabilitySlot
from common.utils.slot import (
    expand_slots,
    validate_and_parse_day_of_week,
    parse_time_field,
    parse_date_field,
    validate_week_start_date,
    validate_day_range,
    is_valid_time_range
)
from datetime import time, date, timedelta
from common.app_logger import get_logger

logger = get_logger(__name__)


class AvailabilitySlotService:

    def __init__(self, config):
        self.config = config

        self.repository_factory = RepositoryFactory(config)
        self.availability_slot_repo = self.repository_factory.get_repository(RepoType.AVAILABILITY_SLOT)

    def save_availability_slot(self, availability_slot: AvailabilitySlot):
        availability_slot = self.availability_slot_repo.save(availability_slot)
        return availability_slot

    def get_availability_slot_by_id(self, entity_id: str):
        availability_slot = self.availability_slot_repo.get_one({"entity_id": entity_id})
        return availability_slot

    def get_availability_slots_by_employee_id(self, employee_id: str):
        availability_slots = self.availability_slot_repo.get_many({"employee_id": employee_id})
        return availability_slots

    def get_availability_slots_by_week(self, employee_id: str, week_start_date: date):
        availability_slots = self.availability_slot_repo.get_many({"employee_id": employee_id})

        return [slot for slot in availability_slots if slot.week_start_date == week_start_date]

    def get_availability_slots_for_organization(self, organization_id: str):
        availability_slots = self.availability_slot_repo.get_employee_availability_slots([organization_id])
        return availability_slots

    def get_availability_slots_for_time_slot(self, start_time: time, end_time: time, visit_date: date, patient_id: str, organization_ids: List[str]) -> List[AvailabilitySlot]:
        """
        Get availability slots for a specific time slot and employee.

        Args:
            start_time: Start time of the patient care slot
            end_time: End time of the patient care slot
            day_of_week: Day of the week (0=Monday, 6=Sunday)
            organization_ids: The organization IDs to filter by

        Returns:
            List of AvailabilitySlot instances that match the criteria
        """
        results = self.availability_slot_repo.get_eligible_availability_slots_by_patient_care_slot(
            start_time=start_time,
            end_time=end_time,
            visit_date=visit_date,
            patient_id=patient_id,
            organization_ids=organization_ids
        )

        def time_to_minutes(t: time) -> int:
            return t.hour * 60 + t.minute

        def midpoint_offset(slot_start, slot_end, target_start, target_end):
            slot_mid = (time_to_minutes(slot_start) + time_to_minutes(slot_end)) / 2
            target_mid = (time_to_minutes(target_start) + time_to_minutes(target_end)) / 2
            return abs(slot_mid - target_mid)

        def classify_slot(slot_start, slot_end, target_start, target_end):
            # Full coverage: slot starts before or at target start, ends after or at target end
            if slot_start <= target_start and slot_end >= target_end:
                return "full"
            # Partial overlap: intervals overlap at all
            elif slot_end > target_start and slot_start < target_end:
                return "partial"
            else:
                return "none"

        for row in results:
            row["match_type"] = classify_slot(
                row["start_time"], row["end_time"], start_time, end_time
            )
            row["offset"] = midpoint_offset(
                row["start_time"], row["end_time"], start_time, end_time
            )

        # Sort: full matches first (match_type == 'full'), then by proximity
        sorted_results = sorted(
            results,
            key=lambda r: (r["match_type"] != "full", r["offset"])
        )

        return [
            {
                "employee_social_security_number": row.pop("employee_social_security_number"),
                "employee_name": row.pop("employee_name"),
                "employee_date_of_birth": row.pop("employee_date_of_birth"),
                "employee_display_id": row.pop("employee_display_id"),
                "offset": row.pop("offset"),
                "match_type": row.pop("match_type"),
                "available_from": row.pop("available_from"),
                "available_to": row.pop("available_to"),
                **AvailabilitySlot(**row).as_dict()
            } for row in sorted_results
        ]

    def delete_employee_availability_slot(self, employee_id: str, slot_id: str, series_id: Optional[str] = None, from_date: Optional[str] = None) -> AvailabilitySlot:
        if series_id and from_date:
            deleted_slots = self.availability_slot_repo.delete_future_patient_care_slots(
                employee_id=employee_id,
                series_id=series_id,
                from_date=from_date
            )
            return deleted_slots
        slot = self.availability_slot_repo.get_one({"entity_id": slot_id, "employee_id": employee_id})
        if not slot:
            raise NotFoundError(f"Availability slot with id '{slot_id}' not found for employee '{employee_id}'")
        slot.active = False
        return self.availability_slot_repo.save(slot)

    def update_availability_slot(self, employee_id: str, slot_id: str, slot_data: dict) -> AvailabilitySlot:
        """
        Update an existing availability slot with partial data.
        
        Args:
            employee_id: The employee's entity_id
            slot_id: The slot's entity_id
            slot_data: Dictionary containing fields to update
            
        Returns:
            The updated AvailabilitySlot
        """
        # Fetch existing slot
        slot = self.availability_slot_repo.get_one({"entity_id": slot_id, "employee_id": employee_id})
        if not slot:
            raise NotFoundError(f"Availability slot with id '{slot_id}' not found for employee '{employee_id}'")
        
        # Update day of week fields if provided
        if 'day_of_week' in slot_data:
            slot.day_of_week = validate_and_parse_day_of_week(slot_data['day_of_week'], "day_of_week", allow_none=True)
        
        if 'start_day_of_week' in slot_data:
            slot.start_day_of_week = validate_and_parse_day_of_week(
                slot_data['start_day_of_week'], "start_day_of_week", allow_none=True
            )
        
        if 'end_day_of_week' in slot_data:
            slot.end_day_of_week = validate_and_parse_day_of_week(
                slot_data['end_day_of_week'], "end_day_of_week", allow_none=True
            )
        
        # Validate day range
        validate_day_range(slot.start_day_of_week, slot.end_day_of_week)
        
        # Update time fields if provided
        if 'start_time' in slot_data:
            slot.start_time = parse_time_field(slot_data['start_time'], "start_time")
        
        if 'end_time' in slot_data:
            slot.end_time = parse_time_field(slot_data['end_time'], "end_time")
        
        # Validate time range
        if not is_valid_time_range(slot.start_time, slot.end_time):
            raise InputValidationError(f"Invalid time range: start_time {slot.start_time} to end_time {slot.end_time}")

        # Update week_start_date if provided
        if 'week_start_date' in slot_data:
            week_start = parse_date_field(slot_data['week_start_date'], "week_start_date", allow_none=False)
            week_start = validate_week_start_date(week_start)
            slot.week_start_date = week_start
            slot.week_end_date = week_start + timedelta(days=6) if week_start else None
        
        # Update start_date and end_date if provided
        if 'start_date' in slot_data:
            slot.start_date = parse_date_field(slot_data['start_date'], "start_date")
        
        if 'end_date' in slot_data:
            slot.end_date = parse_date_field(slot_data['end_date'], "end_date")
        
        logger.info(f"Updating availability slot {slot_id} for employee {employee_id}")
        return self.availability_slot_repo.save(slot)

    def expand_and_save_slots(self, payload, employee_id):
        expanded_slots = expand_slots(
            payload=payload,
            start_date=payload.get('start_date'),
            entity_id=employee_id,
            entity_type='employee'
        )
        saved_slots = []
        for slot in expanded_slots:
            saved_slot = self.availability_slot_repo.save(slot)
            saved_slots.append(saved_slot)
        return saved_slots

    def create_availability_slot(self, data):
        availability_slot = AvailabilitySlot(
            day_of_week=data.get('day_of_week'),
            start_day_of_week=data.get('start_day_of_week'),
            end_day_of_week=data.get('end_day_of_week'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            employee_id=data.get('employee_id'),
            series_id=data.get('series_id', None),
            week_start_date=data.get('week_start_date'),
            week_end_date=data.get('week_end_date'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date')
        )
        return self.availability_slot_repo.save(availability_slot)

    def has_availability_for_slot(self, employee_id: str, day_of_week: int, start_time: time, end_time: time, start_date: str, match_type: str = "exact"):
        """
        Check if there's availability for the given slot criteria and return the logical_key.

        Args:
            employee_id: The employee's entity_id
            day_of_week: Day of the week (0=Monday, 6=Sunday)
            start_time: Start time of the slot
            end_time: End time of the slot
            match_type: "exact" for exact match, "overlap" for any overlap, "contains" if availability contains the slot

        Returns:
            str: logical_key of the matching availability slot, empty string if no match found
        """
        # Get all availability slots for this employee
        existing_slots = self.get_availability_slots_by_employee_id(employee_id)

        # Filter by day of week and active status
        day_slots = [
            slot for slot in existing_slots
            if slot.day_of_week == day_of_week and slot.start_date == start_date and slot.active
        ]

        if not day_slots:
            return None

        for slot in day_slots:
            if match_type == "exact":
                # Exact time match
                if slot.start_time == start_time and slot.end_time == end_time:
                    return slot.logical_key
            elif match_type == "overlap":
                # Any time overlap
                if slot.start_time < end_time and slot.end_time > start_time:
                    return slot.logical_key
            elif match_type == "contains":
                # Availability slot contains the requested time
                if slot.start_time <= start_time and slot.end_time >= end_time:
                    return slot.logical_key

        return None
