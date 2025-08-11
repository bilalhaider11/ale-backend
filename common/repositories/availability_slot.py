from common.repositories.base import BaseRepository
from common.models import AvailabilitySlot
from datetime import time, date, datetime


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

    def get_eligible_availability_slots_by_patient_care_slot(self, start_time: time, end_time: time, visit_date: date, patient_id: str, organization_ids: list[str]) -> list:
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
                slot.employee_id AS employee_id,
                e.employee_id AS employee_display_id,
                e.social_security_number AS employee_social_security_number,
                e.date_of_birth AS employee_date_of_birth,
                ps.first_name || ' ' || ps.last_name AS employee_name,
                -- derive the visible window for this selection
                GREATEST(
                    slot.start_time,
                    COALESCE((
                        SELECT MAX(cv.scheduled_end_time::time)
                        FROM care_visit cv
                        WHERE cv.employee_id = slot.employee_id
                        AND cv.visit_date = %s                 -- visit_date
                        AND cv.active = TRUE
                        -- only bookings that actually end before the target starts
                        AND cv.scheduled_end_time <= %s  -- target_start_time
                    ), slot.start_time)
                ) AS available_from,

                LEAST(
                    slot.end_time,
                    COALESCE((
                        SELECT MIN(cv.scheduled_start_time::time)
                        FROM care_visit cv
                        WHERE cv.employee_id = slot.employee_id
                        AND cv.visit_date = %s                 -- visit_date
                        AND cv.active = TRUE
                        -- next booking that begins after (or at) the target start
                        AND cv.scheduled_start_time >= %s -- target_start_time
                    ), slot.end_time)
                ) AS available_to,

                slot.*
            FROM availability_slot AS slot
            JOIN employee e ON slot.employee_id = e.entity_id
            JOIN person ps ON e.person_id = ps.entity_id
            WHERE slot.day_of_week = %s
            -- any overlap between employee slot and patient slot
            AND slot.start_time < %s   -- patient_end_time
            AND slot.end_time   > %s   -- patient_start_time
            AND e.organization_id IN %s
            AND e.active = true
            AND slot.active = true
            AND slot.logical_key NOT IN (
                SELECT availability_slot_key
                FROM care_visit
                WHERE visit_date = %s
                    -- any overlap between booking and patient slot
                    AND scheduled_start_time < %s  -- patient_end_dt
                    AND scheduled_end_time   > %s  -- patient_start_dt
                    AND active = true
            )
            AND NOT EXISTS (
                SELECT 1
                    FROM care_visit cv
                WHERE cv.visit_date = %s
                AND cv.patient_id = %s
                AND cv.active = true
                AND cv.scheduled_start_time < %s
                AND cv.scheduled_end_time > %s
            )
        """
        params = (
            visit_date,
            start_dt,
            visit_date,
            start_dt,

            visit_date.weekday(), 
            end_time,       # for slot.start_time < patient_end
            start_time,     # for slot.end_time > patient_start
            tuple(organization_ids), 
            visit_date, 
            end_dt,         # for scheduled_start_time < patient_end_dt
            start_dt,       # for scheduled_end_time > patient_start_dt
            visit_date, 
            patient_id,
            end_dt,
            start_dt
        )
        
        with self.adapter:
            result = self.adapter.execute_query(query, params)

        return result
