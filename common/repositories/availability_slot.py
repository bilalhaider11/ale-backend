from common.repositories.base import BaseRepository
from common.models import AvailabilitySlot


class AvailabilitySlotRepository(BaseRepository):
    MODEL = AvailabilitySlot

    def get_availability_slot_by_id(self, entity_id: str) -> AvailabilitySlot:
        return self.get_one({"entity_id": entity_id})

    def get_availability_slots_by_employee_id(self, employee_id: str) -> list[AvailabilitySlot]:
        return self.get_all({"employee_id": employee_id})

    def get_availability_slots_by_day(self, day_of_week: int) -> list[AvailabilitySlot]:
        return self.get_all({"day_of_week": day_of_week})

    def update_availability_slot(self, availability_slot: AvailabilitySlot) -> AvailabilitySlot:
        return self.save(availability_slot)
