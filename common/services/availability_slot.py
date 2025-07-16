from typing import List
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.availability_slot import AvailabilitySlot


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
        for slot in slots_to_add:
            slot.employee_id = employee_id  # Ensure employee_id is set
            self.availability_slot_repo.save(slot)
