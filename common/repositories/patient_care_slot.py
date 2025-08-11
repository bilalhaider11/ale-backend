from common.repositories.base import BaseRepository
from common.models.patient_care_slot import PatientCareSlot
from datetime import time, date, datetime

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

    def get_eligible_patient_care_slots_by_availability_slot(self, start_time: time, end_time: time, visit_date: date, employee_id: str, organization_ids: list[str]) -> list:
        """
        Get patients eligible for a care slot based on availability slot criteria.
        
        Args:
            start_time: Start time of the availability slot
            end_time: End time of the availability slot
            day_of_week: Day of the week (0=Monday, 6=Sunday)
            organization_ids: The organization IDs to filter by

        Returns:
            List of Patient instances that match the criteria
        """

        start_dt = datetime.combine(visit_date, start_time)
        end_dt = datetime.combine(visit_date, end_time)

        query = """
            SELECT 
                pcs.patient_id AS patient_id,
                p.social_security_number AS patient_social_security_number,
                p.date_of_birth AS patient_date_of_birth,
                ps.first_name || ' ' || ps.last_name AS patient_name,
                pcs.*
            FROM patient_care_slot pcs
            JOIN patient p ON pcs.patient_id = p.entity_id
            JOIN person ps ON p.person_id = ps.entity_id
            WHERE pcs.day_of_week = %s
            AND pcs.end_time > %s
            AND pcs.start_time < %s
            AND p.organization_id IN %s
            AND p.active = true
            AND pcs.active = true
            AND %s >= p.care_period_start
            AND (%s <= p.care_period_end OR p.care_period_end IS NULL)
            AND pcs.logical_key NOT IN (
                SELECT patient_care_slot_key
                FROM care_visit
                WHERE visit_date = %s
                AND scheduled_end_time > %s
                AND scheduled_start_time < %s
                AND active = true
            )
            AND NOT EXISTS (
                SELECT 1
                FROM care_visit cv
                WHERE cv.visit_date = %s
                    AND cv.employee_id = %s
                    AND cv.active = true
                    AND cv.scheduled_end_time > (timestamp %s + pcs.start_time)
                    AND cv.scheduled_start_time < (timestamp %s + pcs.end_time)
            );
        """
        params = (
            visit_date.weekday(), 
            start_time, 
            end_time, 
            tuple(organization_ids), 
            visit_date, 
            visit_date, 
            visit_date, 
            start_dt, 
            end_dt, 
            visit_date, 
            employee_id, 
            visit_date, 
            visit_date
        )
        
        with self.adapter:
            result = self.adapter.execute_query(query, params)

        return result
