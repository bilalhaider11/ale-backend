from typing import List, Dict, Optional
from datetime import date, time, timedelta
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.patient_care_slot import PatientCareSlot
from common.app_logger import get_logger
from common.helpers.exceptions import InputValidationError, NotFoundError
from common.utils.slot import (
    expand_slots,
    validate_and_parse_day_of_week,
    parse_time_field,
    parse_date_field,
    validate_week_start_date,
    validate_day_range,
    is_valid_time_range
)

logger = get_logger(__name__)


class PatientCareSlotService:

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.patient_care_slot_repo = self.repository_factory.get_repository(RepoType.PATIENT_CARE_SLOT)

    def save_patient_care_slot(self, patient_care_slot: PatientCareSlot):
        patient_care_slot = self.patient_care_slot_repo.save(patient_care_slot)
        return patient_care_slot

    def get_patient_care_slots_by_week(self, patient_id: str, week_start_date: date):
        """Get all care slots for a patient in a specific week."""
        # Get all slots for the patient first
        patient_slots = self.patient_care_slot_repo.get_many({
            "patient_id": patient_id
        })

        # Then filter for the specific week in Python
        return [slot for slot in patient_slots if slot.week_start_date == week_start_date]


    def get_patient_care_slots_by_patient_id(self, patient_id: str) -> List[PatientCareSlot]:
        """
        Get all care slots for a specific patient.
        """
        return self.patient_care_slot_repo.get_many({
            "patient_id": patient_id
        })


    def get_patient_care_slots_for_time_slot(self, start_time: time, end_time: time, 
                                  visit_date: date, employee_id: str, organization_ids: List[str]) -> List[PatientCareSlot]:
        """
        Get patients eligible for a care slot based on availability slot criteria.
        
        Args:
            start_time: Start time of the availability slot
            end_time: End time of the availability slot
            day_of_week: Day of the week (0=Monday, 6=Sunday)
            organization_ids: The organization IDs to filter by

        Returns:
            List of PatientCareSlot instances that match the criteria
        """
        results = self.patient_care_slot_repo.get_eligible_patient_care_slots_by_availability_slot(
            start_time=start_time,
            end_time=end_time,
            visit_date=visit_date,
            employee_id=employee_id,
            organization_ids=organization_ids
        )

        def time_to_minutes(t: time) -> int:
            return t.hour * 60 + t.minute

        def midpoint_offset(slot_start, slot_end, target_start, target_end):
            slot_mid = (time_to_minutes(slot_start) + time_to_minutes(slot_end)) / 2
            target_mid = (time_to_minutes(target_start) + time_to_minutes(target_end)) / 2
            return abs(slot_mid - target_mid)

        def classify_slot(slot_start, slot_end, target_start, target_end):
            if slot_start >= target_start and slot_end <= target_end:
                return "full"
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
                "patient_name": row.pop("patient_name"),
                "offset": row.pop("offset"),
                "match_type": row.pop("match_type"),
                **PatientCareSlot(**{k: v for k, v in row.items() if k in PatientCareSlot.__annotations__}).as_dict()
            } for row in sorted_results
        ]

    def get_patient_care_slots_for_organization(self, organization_id: str):
        return self.patient_care_slot_repo.get_patient_care_slots_by_organization(organization_id)
    
    def _calculate_total_hours(self, slots: List[PatientCareSlot]) -> float:
        """Calculate total hours from a list of slots."""
        total_minutes = 0
        for slot in slots:
            if slot.start_time and slot.end_time:
                total_minutes += self._calculate_slot_duration_minutes(slot.start_time, slot.end_time)
        return total_minutes / 60
    
    def _validate_weekly_quota(self, patient_weekly_quota: Optional[float], new_slot: PatientCareSlot, 
                               existing_slots: List[PatientCareSlot], exclude_slot_id: Optional[str] = None) -> None:
        """
        Validate that adding/updating a slot doesn't exceed the patient's weekly quota.
        
        Args:
            patient_weekly_quota: The patient's weekly quota in hours (None means no limit)
            new_slot: The slot being created or updated
            existing_slots: Existing slots for the same week
            exclude_slot_id: Optional slot ID to exclude from calculation (for updates)
        
        Raises:
            InputValidationError: If weekly quota would be exceeded
        """
        # Skip validation if patient has no quota set
        if patient_weekly_quota is None or patient_weekly_quota == 0:
            return
        
        # Filter out the slot being updated
        slots_to_count = [slot for slot in existing_slots 
                         if not (exclude_slot_id and slot.entity_id == exclude_slot_id)]
        
        # Add the new/updated slot
        slots_to_count.append(new_slot)
        
        # Calculate total hours
        total_hours = self._calculate_total_hours(slots_to_count)
        
        # Validate against quota
        if total_hours > patient_weekly_quota:
            raise InputValidationError(
                f"Weekly quota exceeded: total would be {total_hours:.2f}h, limit is {patient_weekly_quota}h"
            )
    
    def _calculate_slot_duration_minutes(self, start_time: time, end_time: time) -> int:
        """Calculate slot duration in minutes, handling overnight slots."""
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute
        
        if end_minutes > start_minutes:
            # Regular same-day slot
            return end_minutes - start_minutes
        else:
            # Overnight slot - calculate duration across midnight
            return (24 * 60 - start_minutes) + end_minutes

    def delete_patient_care_slot(self, patient_id: str, slot_id: str, series_id: Optional[str] = None, from_date: Optional[str] = None) -> PatientCareSlot:
        if series_id and from_date:
            deleted_slots = self.patient_care_slot_repo.delete_future_patient_care_slots(
                patient_id=patient_id,
                series_id=series_id,
                from_date=from_date
            )
            return deleted_slots
        slot = self.patient_care_slot_repo.get_one({"entity_id": slot_id, "patient_id": patient_id})
        if not slot:
            raise NotFoundError(f"Patient care slot with id '{slot_id}' not found for patient '{patient_id}'")
        slot.active = False
        return self.patient_care_slot_repo.save(slot)

    def update_patient_care_slot(self, patient_id: str, slot_id: str, slot_data: dict, patient_weekly_quota: Optional[float] = None) -> PatientCareSlot:
        """
        Update an existing patient care slot with partial data.
        
        Args:
            patient_id: The patient's entity_id
            slot_id: The slot's entity_id
            slot_data: Dictionary containing fields to update
            patient_weekly_quota: Optional patient weekly quota for validation
            
        Returns:
            The updated PatientCareSlot
        """
        # Fetch existing slot
        slot = self.patient_care_slot_repo.get_one({"entity_id": slot_id, "patient_id": patient_id})
        if not slot:
            raise NotFoundError(f"Patient care slot with id '{slot_id}' not found for patient '{patient_id}'")
        
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

        if patient_weekly_quota is None or patient_weekly_quota == 0:
            raise InputValidationError("Please set a weekly quota before adding care slots.")
        
        # Validate weekly quota if provided
        week_start_date = slot.week_start_date
        existing_slots = self.get_patient_care_slots_by_week(patient_id, week_start_date) if week_start_date else []
        self._validate_weekly_quota(patient_weekly_quota, slot, existing_slots, exclude_slot_id=slot_id)
        
        logger.info(f"Updating patient care slot {slot_id} for patient {patient_id}")
        return self.patient_care_slot_repo.save(slot)

    def get_slots_by_logical_key(self, logical_key: str, patient_id: str) -> List[PatientCareSlot]:
        """Get all slots with the same logical_key for a patient."""
        return self.patient_care_slot_repo.get_many({
            "logical_key": logical_key,
            "patient_id": patient_id,
            "active": True
        })

    def expand_and_save_slots(self, payload, patient_id):
        expanded_slots = expand_slots(
            payload=payload,
            start_date=payload.get('start_date'),
            entity_id=patient_id,
            entity_type='patient'
        )
        saved_slots = []
        for slot in expanded_slots:
            saved_slot = self.patient_care_slot_repo.save(slot)
            saved_slots.append(saved_slot)
        return saved_slots
