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
        
        # Create sets of keys for comparison using (day_of_week, start_time, end_time)
        existing_keys = {(slot.day_of_week, slot.start_time, slot.end_time) for slot in existing_slots}
        new_keys = {(slot.day_of_week, slot.start_time, slot.end_time) for slot in slots}
        
        # Create mappings from keys to slots for easy lookup
        existing_slots_map = {(slot.day_of_week, slot.start_time, slot.end_time): slot for slot in existing_slots}
        new_slots_map = {(slot.day_of_week, slot.start_time, slot.end_time): slot for slot in slots}
        
        # Compute slots_to_delete: existing slots not in new slots
        keys_to_delete = existing_keys - new_keys
        slots_to_delete = [existing_slots_map[key] for key in keys_to_delete]
        
        # Compute slots_to_add: new slots not in existing slots
        keys_to_add = new_keys - existing_keys
        slots_to_add = [new_slots_map[key] for key in keys_to_add]
        
        # Delete all slots_to_delete from the database
        for slot in slots_to_delete:
            self.patient_care_slot_repo.delete(slot)
        
        # Save all slots_to_add to the database
        for slot in slots_to_add:
            slot.patient_id = patient_id
            slot.week_start_date = week_start_date
            slot.week_end_date = week_end_date
            # Validate day_of_week
            if not (0 <= slot.day_of_week <= 6):
                raise ValueError(f"day_of_week must be between 0 and 6, got {slot.day_of_week}")
            # Validate time order
            if slot.start_time >= slot.end_time:
                raise ValueError(f"start_time must be before end_time")
            self.patient_care_slot_repo.save(slot)
        
        # Return the weekly duration for the patient
        return self.get_patient_care_slots_by_week(patient_id, week_start_date)

    def apply_consistent_slots_to_days(self, patient_id: str, selected_days: List[int], 
                                      consistent_slots: List[Dict], week_start_date: date, 
                                      week_end_date: date) -> List[PatientCareSlot]:
        """Apply consistent time slots to all selected days for a specific week."""
        slots = []
        for day in selected_days:
            for slot_data in consistent_slots:
                slot = PatientCareSlot(
                    patient_id=patient_id,
                    day_of_week=day,
                    start_time=slot_data['start_time'],
                    end_time=slot_data['end_time'],
                    week_start_date=week_start_date,
                    week_end_date=week_end_date,
                    is_consistent_slot=True
                )
                slots.append(slot)
        
        return slots

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
                'is_consistent_slot': slot.is_consistent_slot
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
            if not slot.start_time or not slot.end_time:
                continue
            start_minutes = slot.start_time.hour * 60 + slot.start_time.minute
            end_minutes = slot.end_time.hour * 60 + slot.end_time.minute

            if end_minutes > start_minutes:
                total_minutes += end_minutes - start_minutes

        hours, minutes = divmod(total_minutes, 60)
        return f"{int(hours):02d}H:{int(minutes):02d}M"
