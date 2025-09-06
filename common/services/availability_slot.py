from typing import List
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.availability_slot import AvailabilitySlot
from datetime import time, date


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

    def get_availability_slots_for_organization(self, organization_id: str):
        availability_slots = self.availability_slot_repo.get_employee_availability_slots([organization_id])
        return availability_slots

    def upsert_availability_slots(self, employee_id: str, slots: List[AvailabilitySlot]):
        # Fetch all existing availability slots for the given employee_id
        existing_slots = self.get_availability_slots_by_employee_id(employee_id)
        
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
            self.availability_slot_repo.delete(slot)

        # Save all slots_to_add to the database
        added_slots = []
        for slot in slots_to_add:
            slot.employee_id = employee_id  # Ensure employee_id is set
            added_slot = self.availability_slot_repo.save(slot)
            added_slots.append(added_slot)

        return added_slots

    def get_availability_slots_for_time_slot(self, start_time: time, end_time: time, 
                                  visit_date: date, patient_id: str, organization_ids: List[str]) -> List[AvailabilitySlot]:
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