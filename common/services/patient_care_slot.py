from typing import List, Dict, Optional, Any
from datetime import date, time, timedelta, datetime
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.patient_care_slot import PatientCareSlot
from common.app_logger import get_logger
from common.helpers.exceptions import InputValidationError, NotFoundError
from common.utils.slot import expand_slots

logger = get_logger(__name__)


class PatientCareSlotService:

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.patient_care_slot_repo = self.repository_factory.get_repository(RepoType.PATIENT_CARE_SLOT)
        
        # Constants for validation
        self.MIN_DAY_OF_WEEK = 0
        self.MAX_DAY_OF_WEEK = 6

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

    def _is_valid_time_range(self, start_time: time, end_time: time) -> bool:
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

    def _validate_and_parse_day_of_week(self, value: Any, field_name: str = "day_of_week", allow_none: bool = False) -> Optional[int]:
        """Validate and return day of week value."""
        if value is None:
            if allow_none:
                return None
            raise InputValidationError(f"{field_name} is required")
        
        if not isinstance(value, int) or not (self.MIN_DAY_OF_WEEK <= value <= self.MAX_DAY_OF_WEEK):
            raise InputValidationError(
                f"{field_name} must be an integer between {self.MIN_DAY_OF_WEEK} and {self.MAX_DAY_OF_WEEK}"
            )
        return value
    
    def _parse_time_field(self, value: Any, field_name: str) -> time:
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
    
    def _parse_date_field(self, value: Any, field_name: str, allow_none: bool = True) -> Optional[date]:
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
    
    def _validate_week_start_date(self, week_start_date: Optional[date]) -> Optional[date]:
        """Validate that week_start_date is a Monday."""
        if week_start_date and week_start_date.weekday() != 0:
            raise InputValidationError("week_start_date must be a Monday")
        return week_start_date
    
    def _validate_day_range(self, start_day: Optional[int], end_day: Optional[int]) -> None:
        """Validate that day range is valid."""
        if start_day is not None and end_day is not None:
            if start_day > end_day and not (start_day == 6 and end_day == 0):
                raise InputValidationError("start_day_of_week cannot be greater than end_day_of_week")
    
    def _parse_slot_data(self, slot_data: dict) -> PatientCareSlot:
        """Parse and validate slot data into a PatientCareSlot object (DRY helper)."""
        # Validate required fields
        required_fields = ["day_of_week", "start_day_of_week", "end_day_of_week", "start_time", "end_time"]
        missing_fields = [field for field in required_fields if field not in slot_data]
        if missing_fields:
            raise InputValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Parse and validate all fields
        day_of_week = self._validate_and_parse_day_of_week(slot_data.get('day_of_week'), "day_of_week")
        start_day_of_week = self._validate_and_parse_day_of_week(slot_data.get('start_day_of_week'), "start_day_of_week")
        end_day_of_week = self._validate_and_parse_day_of_week(slot_data.get('end_day_of_week'), "end_day_of_week")
        
        self._validate_day_range(start_day_of_week, end_day_of_week)
        
        start_time = self._parse_time_field(slot_data['start_time'], "start_time")
        end_time = self._parse_time_field(slot_data['end_time'], "end_time")
        
        if not self._is_valid_time_range(start_time, end_time):
            raise InputValidationError(f"Invalid time range: start_time {start_time} to end_time {end_time}")
        
        week_start_date = self._parse_date_field(slot_data.get('week_start_date'), "week_start_date", allow_none=False)
        week_start_date = self._validate_week_start_date(week_start_date)
        week_end_date = week_start_date + timedelta(days=6) if week_start_date else None
        
        start_date = self._parse_date_field(slot_data.get('start_date'), "start_date")
        end_date = self._parse_date_field(slot_data.get('end_date'), "end_date")
        
        return PatientCareSlot(
            patient_id="",  # Will be set by caller
            day_of_week=day_of_week,
            start_day_of_week=start_day_of_week,
            end_day_of_week=end_day_of_week,
            start_time=start_time,
            end_time=end_time,
            week_start_date=week_start_date,
            week_end_date=week_end_date,
            start_date=start_date,
            end_date=end_date
        )
    
    def create_patient_care_slots(self, patient_id: str, slots_data: List[dict], patient_weekly_quota: Optional[float] = None) -> List[PatientCareSlot]:
        """
        Create multiple patient care slots with optimized quota validation.
        
        Args:
            patient_id: The patient's entity_id
            slots_data: List of slot data dictionaries
            patient_weekly_quota: Optional patient weekly quota for validation
            
        Returns:
            List of created PatientCareSlot objects
        """
        if not slots_data:
            raise InputValidationError("At least one slot must be provided")
            
        if patient_weekly_quota is None or patient_weekly_quota == 0:
            raise InputValidationError("Please set a weekly quota before adding care slots.")
        
        # Parse all slots using DRY helper
        parsed_slots = []
        for slot_data in slots_data:
            if not isinstance(slot_data, dict):
                raise InputValidationError("Each slot must be a JSON object")
            
            slot = self._parse_slot_data(slot_data)
            slot.patient_id = patient_id
            parsed_slots.append(slot)
        
        # Validate quota for each week separately
        # Group slots by week for proper quota validation
        slots_by_week = {}
        for slot in parsed_slots:
            week_start = slot.week_start_date
            if week_start not in slots_by_week:
                slots_by_week[week_start] = []
            slots_by_week[week_start].append(slot)
        
        # Validate quota for each week using existing helper method
        for week_start, week_slots in slots_by_week.items():
            # Get existing slots for this week
            existing_slots = self.get_patient_care_slots_by_week(patient_id, week_start)
            
            # Validate each slot in this week using the existing helper
            for slot in week_slots:
                self._validate_weekly_quota(patient_weekly_quota, slot, existing_slots)
        
        # Save all slots
        saved_slots = [self.patient_care_slot_repo.save(slot) for slot in parsed_slots]
        
        logger.info(f"Created {len(saved_slots)} patient care slots for patient {patient_id}")
        return saved_slots
    
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
            slot.day_of_week = self._validate_and_parse_day_of_week(slot_data['day_of_week'], "day_of_week", allow_none=True)
        
        if 'start_day_of_week' in slot_data:
            slot.start_day_of_week = self._validate_and_parse_day_of_week(
                slot_data['start_day_of_week'], "start_day_of_week", allow_none=True
            )
        
        if 'end_day_of_week' in slot_data:
            slot.end_day_of_week = self._validate_and_parse_day_of_week(
                slot_data['end_day_of_week'], "end_day_of_week", allow_none=True
            )
        
        # Validate day range
        self._validate_day_range(slot.start_day_of_week, slot.end_day_of_week)
        
        # Update time fields if provided
        if 'start_time' in slot_data:
            slot.start_time = self._parse_time_field(slot_data['start_time'], "start_time")
        
        if 'end_time' in slot_data:
            slot.end_time = self._parse_time_field(slot_data['end_time'], "end_time")
        
        # Validate time range
        if not self._is_valid_time_range(slot.start_time, slot.end_time):
            raise InputValidationError(f"Invalid time range: start_time {slot.start_time} to end_time {slot.end_time}")

        # Update week_start_date if provided
        if 'week_start_date' in slot_data:
            week_start_date = self._parse_date_field(slot_data['week_start_date'], "week_start_date", allow_none=False)
            week_start_date = self._validate_week_start_date(week_start_date)
            slot.week_start_date = week_start_date
            slot.week_end_date = week_start_date + timedelta(days=6) if week_start_date else None
        
        # Update start_date and end_date if provided
        if 'start_date' in slot_data:
            slot.start_date = self._parse_date_field(slot_data['start_date'], "start_date")
        
        if 'end_date' in slot_data:
            slot.end_date = self._parse_date_field(slot_data['end_date'], "end_date")

        if patient_weekly_quota is None or patient_weekly_quota == 0:
            raise InputValidationError("Please set a weekly quota before adding care slots.")
        
        # Validate weekly quota if provided
        week_start_date = slot.week_start_date
        existing_slots = self.get_patient_care_slots_by_week(patient_id, week_start_date) if week_start_date else []
        self._validate_weekly_quota(patient_weekly_quota, slot, existing_slots, exclude_slot_id=slot_id)
        
        logger.info(f"Updating patient care slot {slot_id} for patient {patient_id}")
        return self.patient_care_slot_repo.save(slot)

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
