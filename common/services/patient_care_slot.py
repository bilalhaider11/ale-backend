from typing import List, Dict
from datetime import date, time, timedelta
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.patient_care_slot import PatientCareSlot
from common.app_logger import get_logger

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

    def upsert_patient_care_slots(self, patient_id: str, slots: List[PatientCareSlot], 
                                  week_start_date: date = None, week_end_date: date = None):
        
        # Fetch existing slots for this patient and week
        patient_slots = self.patient_care_slot_repo.get_many({
            "patient_id": patient_id
        })
        
        # Then filter for the specific week in Python
        existing_slots = [slot for slot in patient_slots if slot.week_start_date == week_start_date]
        
        # Create sets of keys for comparison using (day_of_week, start_day_of_week, end_day_of_week, start_time, end_time)
        existing_keys = {(slot.day_of_week, slot.start_day_of_week, slot.end_day_of_week, slot.start_time, slot.end_time) for slot in existing_slots}
        new_keys = {(slot.day_of_week, slot.start_day_of_week, slot.end_day_of_week, slot.start_time, slot.end_time) for slot in slots}
        
        # Create mappings from keys to slots for easy lookup
        existing_slots_map = {(slot.day_of_week, slot.start_day_of_week, slot.end_day_of_week, slot.start_time, slot.end_time): slot for slot in existing_slots}
        new_slots_map = {(slot.day_of_week, slot.start_day_of_week, slot.end_day_of_week, slot.start_time, slot.end_time): slot for slot in slots}
        
        # Compute slots_to_delete: existing slots not in new slots
        keys_to_delete = existing_keys - new_keys
        slots_to_delete = [existing_slots_map[key] for key in keys_to_delete]
        
        # Compute slots_to_add: new slots not in existing slots
        keys_to_add = new_keys - existing_keys
        slots_to_add = [new_slots_map[key] for key in keys_to_add]
        
        # Delete all slots_to_delete from the database
        for slot in slots_to_delete:
            try:
                logger.info(f"Deleting patient care slot {slot.entity_id} for patient {patient_id}")
                self.patient_care_slot_repo.delete(slot)
            except Exception as e:
                logger.error(f"Error deleting patient care slot {slot.entity_id}: {str(e)}")
                raise
        
        # Save all slots_to_add to the database
        for slot in slots_to_add:
            try:
                slot.patient_id = patient_id
                slot.week_start_date = week_start_date
                slot.week_end_date = week_end_date
                
                # Validate and save slot
                self._validate_slot(slot)
                logger.info(f"Saving new patient care slot for patient {patient_id}")
                self.patient_care_slot_repo.save(slot)
            except Exception as e:
                logger.error(f"Error saving patient care slot for patient {patient_id}: {str(e)}")
                raise
        
        # Return the weekly duration for the patient
        return self.get_patient_care_slots_by_week(patient_id, week_start_date)

    def get_patient_care_slots_by_week(self, patient_id: str, week_start_date: date):
        """Get all care slots for a patient in a specific week."""
        # Get all slots for the patient first
        patient_slots = self.patient_care_slot_repo.get_many({
            "patient_id": patient_id
        })
        
        # Then filter for the specific week in Python
        return [slot for slot in patient_slots if slot.week_start_date == week_start_date]

    def get_slots_grouped_by_day(self, patient_id: str, week_start_date: date = None) -> Dict[int, List[Dict]]:
        """
        Get patient care slots grouped by day of week.
        
        Returns:
            Dictionary with day numbers as keys and list of slot info as values
        """
        slots = self.get_patient_care_slots_by_week(patient_id, week_start_date)
        
        slots_by_day = {}
        for slot in slots:
            if slot.day_of_week not in slots_by_day:
                slots_by_day[slot.day_of_week] = []
            
            slots_by_day[slot.day_of_week].append({
                'entity_id': slot.entity_id,
                'start_time': slot.start_time,
                'end_time': slot.end_time,
                'start_day_of_week': slot.start_day_of_week,
                'end_day_of_week': slot.end_day_of_week,
            })
        
        # Sort slots within each day by start time
        for day in slots_by_day:
            slots_by_day[day].sort(key=lambda x: x['start_time'])
        
        return slots_by_day

    def calculate_total_weekly_duration(self, patient_id: str, week_start_date) -> str:
        """
        Calculate total weekly duration from all slots.

        Returns:
            A string in the format "HHH...H:MM M", e.g., "02H:05M"
        """
        slots = self.get_patient_care_slots_by_week(patient_id, week_start_date)

        total_minutes = 0
        for slot in slots:
            if slot.start_time and slot.end_time:
                total_minutes += self._calculate_slot_duration_minutes(slot.start_time, slot.end_time)

        hours, minutes = divmod(total_minutes, 60)
        return f"{int(hours):02d}H:{int(minutes):02d}M"


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
    
    def check_weekly_quota(self, slots: List[PatientCareSlot]) -> float:
        """Calculate total hours for weekly quota validation."""
        total_minutes = 0
        for slot in slots:
            if slot.start_time and slot.end_time:
                total_minutes += self._calculate_slot_duration_minutes(slot.start_time, slot.end_time)
        return total_minutes / 60

    def get_patient_care_slots_for_organization(self, organization_id: str):
        return self.patient_care_slot_repo.get_patient_care_slots_by_organization(organization_id)
    
    def _validate_slot(self, slot: PatientCareSlot) -> None:
        """Validate a patient care slot."""
        # Validate day_of_week
        if not (self.MIN_DAY_OF_WEEK <= slot.day_of_week <= self.MAX_DAY_OF_WEEK):
            raise ValueError(f"day_of_week must be between {self.MIN_DAY_OF_WEEK} and {self.MAX_DAY_OF_WEEK}, got {slot.day_of_week}")
        
        # Validate start_day_of_week
        if not (self.MIN_DAY_OF_WEEK <= slot.start_day_of_week <= self.MAX_DAY_OF_WEEK):
            raise ValueError(f"start_day_of_week must be between {self.MIN_DAY_OF_WEEK} and {self.MAX_DAY_OF_WEEK}, got {slot.start_day_of_week}")
        
        # Validate end_day_of_week
        if not (self.MIN_DAY_OF_WEEK <= slot.end_day_of_week <= self.MAX_DAY_OF_WEEK):
            raise ValueError(f"end_day_of_week must be between {self.MIN_DAY_OF_WEEK} and {self.MAX_DAY_OF_WEEK}, got {slot.end_day_of_week}")
        
        # Validate day range
        if slot.start_day_of_week > slot.end_day_of_week:
            raise ValueError(f"start_day_of_week ({slot.start_day_of_week}) cannot be greater than end_day_of_week ({slot.end_day_of_week})")
        
        # Validate time range
        if not self._is_valid_time_range(slot.start_time, slot.end_time):
            raise ValueError(f"Invalid time range: start_time {slot.start_time} to end_time {slot.end_time}")
    
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
            duration_minutes = (24 * 60 - start_minutes) + end_minutes
            # Check if it's a reasonable overnight slot
            # Start should be late evening (8 PM or later) and end should be early morning (8 AM or earlier)
            is_reasonable_overnight = (
                (start_time.hour >= 17 or start_time.hour <= 7) and  # Start between 5 PM and 7 AM
                end_time.hour <= 8  # End at 8 AM or earlier
            )
            return 0 < duration_minutes <= 24 * 60 and is_reasonable_overnight
        else:
            # Regular same-day slot - start must be before end
            return start_minutes < end_minutes
