from common.repositories.base import BaseRepository
from common.models.patient_care_slot import PatientCareSlot


class PatientCareSlotRepository(BaseRepository):
    MODEL = PatientCareSlot

    def get_patient_care_slot_by_id(self, entity_id: str) -> PatientCareSlot:
        return self.get_one({"entity_id": entity_id})

    def get_patient_care_slots_by_patient_id(self, patient_id: str) -> list[PatientCareSlot]:
        return self.get_all({"patient_id": patient_id})

    def get_patient_care_slots_by_day(self, day_of_week: int) -> list[PatientCareSlot]:
        return self.get_all({"day_of_week": day_of_week})

    def update_patient_care_slot(self, patient_care_slot: PatientCareSlot) -> PatientCareSlot:
        return self.save(patient_care_slot)
