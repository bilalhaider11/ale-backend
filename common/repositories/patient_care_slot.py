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

    def get_patient_care_slots_by_organization(self, organization_id: str) -> list:
        """
        Get all patient care slots for patients within a given organization,
        including their care visits and the employee handling each visit.
        """

        query = """
            SELECT 
                p.entity_id AS patient_id,
                per.first_name AS patient_first_name,
                per.last_name AS patient_last_name,
                pcs.entity_id AS slot_id,
                pcs.start_time,
                pcs.end_time,
                pcs.day_of_week,
                pcs.logical_key,
                cv.visit_date,
                cv.employee_id,
                cv.status,
                e.first_name AS employee_first_name,
                e.last_name AS employee_last_name
            FROM patient p
            JOIN person per 
                ON p.person_id = per.entity_id
            JOIN patient_care_slot pcs 
                ON p.entity_id = pcs.patient_id
            LEFT JOIN care_visit cv
                ON pcs.logical_key = cv.patient_care_slot_key
                AND cv.active = true
            LEFT JOIN employee e
                ON cv.employee_id = e.entity_id
            WHERE p.organization_id = %s
              AND p.active = true
              AND pcs.active = true
            ORDER BY per.first_name, per.last_name, pcs.start_time;
        """
        params = (organization_id,)

        with self.adapter:
            rows = self.adapter.execute_query(query, params)

        if not rows:
            return []

        slots_map = {}
        for row in rows:
            slot_id = row["slot_id"]

            if slot_id not in slots_map:
                slots_map[slot_id] = {
                    "patient_id": row["patient_id"],
                    "first_name": row["patient_first_name"],
                    "last_name": row["patient_last_name"],
                    "slot_id": slot_id,
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "day_of_week": row["day_of_week"],
                    "logical_key": row["logical_key"],
                    "care_visits": []
                }

            if row.get("visit_date"):  # only if care visit exists
                slots_map[slot_id]["care_visits"].append({
                    "visit_date": row["visit_date"],
                    "status": row["status"],
                    "employee_id": row["employee_id"],
                    "employee_first_name": row["employee_first_name"],
                    "employee_last_name": row["employee_last_name"]
                })

        return list(slots_map.values())