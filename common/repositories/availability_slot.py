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
                        JOIN availability_slot avs_sub ON cv.availability_slot_id = avs_sub.entity_id
                        WHERE avs_sub.employee_id = slot.employee_id
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
                        JOIN availability_slot avs_sub ON cv.availability_slot_id = avs_sub.entity_id
                        WHERE avs_sub.employee_id = slot.employee_id
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
            AND slot.entity_id NOT IN (
                SELECT availability_slot_id
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
                JOIN patient_care_slot pcs_inner ON cv.patient_care_slot_id = pcs_inner.entity_id
                WHERE cv.visit_date = %s
                AND pcs_inner.patient_id = %s
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

    def get_employee_availability_slots(self, organization_ids: list[str], start_date: date = None, end_date: date = None):
        """
        Fetch all availability slots of employees in the given organizations,
        including employee details and their care visits (with patient first/last name).
        Returns flattened structure with care visit data at the root level.
        """
        query = """                                                                                                                                                                                                                                                                                                    
            SELECT
                e.entity_id AS employee_id,                                                                                                                                                                                                                                                                            
                emp_per.first_name,                                                                                                                                                                                                                                                                                          
                emp_per.last_name,                                                                                                                                                                                                                                                                                           
                s.entity_id AS slot_id,                                                                                                                                                                                                                                                                                
                s.start_time,                                                                                                                                                                                                                                                                                          
                s.end_time,                                                                                                                                                                                                                                                                                            
                s.day_of_week,                                                                                                                                                                                                                                                                                         
                s.start_day_of_week,                                                                                                                                                                                                                                                                                   
                s.end_day_of_week,                                                                                                                                                                                                                                                                                     
                s.start_date,                                                                                                                                                                                                                                                                                          
                s.end_date,                                                                                                                                                                                                                                                                                            
                s.series_id,                                                                                                                                                                                                                                                                                           
                cv.visit_date,                                                                                                                                                                                                                                                                                         
                pcs.patient_id,                                                                                                                                                                                                                                                                                         
                cv.availability_slot_id,                                                                                                                                                                                                                                                                              
                cv.status,                                                                                                                                                                                                                                                                                             
                pat_per.first_name AS patient_first_name,                                                                                                                                                                                                                                                                  
                pat_per.last_name AS patient_last_name                                                                                                                                                                                                                                                                     
            FROM employee e
            JOIN person emp_per
                ON e.person_id = emp_per.entity_id                                                                                                                                                                                                                                                                                            
            JOIN availability_slot s                                                                                                                                                                                                                                                                                   
                ON e.entity_id = s.employee_id                                                                                                                                                                                                                                                                         
            LEFT JOIN care_visit cv                                                                                                                                                                                                                                                                                    
                ON s.entity_id = cv.availability_slot_id                                                                                                                                                                                                                                                            
                AND cv.active = true
            LEFT JOIN patient_care_slot pcs
                ON cv.patient_care_slot_id = pcs.entity_id                                                                                                                                                                                                                                                                                   
            LEFT JOIN patient p                                                                                                                                                                                                                                                                                        
                ON pcs.patient_id = p.entity_id                                                                                                                                                                                                                                                                         
            LEFT JOIN person pat_per                                                                                                                                                                                                                                                                                       
                ON p.person_id = pat_per.entity_id                                                                                                                                                                                                                                                                         
            WHERE e.organization_id IN %s                                                                                                                                                                                                                                                                              
              AND s.active = true                                                                                                                                                                                                                                                                                      
        """
        params = [tuple(organization_ids)]

        # Add date range filtering
        if start_date:
            query += " AND (s.end_date IS NULL OR s.end_date >= %s)"
            params.append(start_date)

        if end_date:
            query += " AND (s.start_date IS NULL OR s.start_date <= %s)"
            params.append(end_date)

        with self.adapter:
            rows = self.adapter.execute_query(query, tuple(params))

        if not rows:
            return []
            # Return flattened structure - each row represents one slot with optional care visit data
        result = []
        for row in rows:
            # Combine patient first and last name into assignee
            assignee = None
            if row["patient_first_name"] and row["patient_last_name"]:
                assignee = f"{row['patient_first_name']} {row['patient_last_name']}"
            elif row["patient_first_name"]:
                assignee = row["patient_first_name"]
            elif row["patient_last_name"]:
                assignee = row["patient_last_name"]

            slot_data = {
                "employee_id": row["employee_id"],
                "series_id": row["series_id"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "slot_id": row["slot_id"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "day_of_week": row["day_of_week"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "start_day_of_week": row["start_day_of_week"],
                "end_day_of_week": row["end_day_of_week"],
                "visit_date": row["visit_date"],
                "assignee_id": row["patient_id"],
                "assignee": assignee,
                "availability_slot_id": row["availability_slot_id"],
                "status": row["status"]
            }
            result.append(slot_data)

        return result

    def delete_future_availability_slots(self, employee_id: str, series_id: str, from_date: str) -> int:
        """
        Soft delete all employee slots from this date forward within the same series.
        """
        query = """
            UPDATE availability_slot
            SET active = false
            WHERE employee_id = %s
              AND series_id = %s
              AND start_date >= %s
              AND active = true
        """
        params = (employee_id, series_id, from_date)

        with self.adapter:
            rows = self.adapter.execute_query(query, params) or []

        return len(rows)

