from datetime import datetime
from typing import List, Union, Dict, Any
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.care_visit import CareVisit, CareVisitStatusEnum

class CareVisitService:

    def __init__(self, config):
        self.config = config

        self.repository_factory = RepositoryFactory(config)
        self.care_visit_repo = self.repository_factory.get_repository(RepoType.CARE_VISIT)

    def get_employee_care_visits_by_date_range(self, start_date, end_date, employee_id):
        return self.care_visit_repo.get_care_visits(
            start_date=start_date,
            end_date=end_date,
            employee_id=employee_id
        )

    def get_patient_care_visits_by_date_range(self, start_date, end_date, patient_id):
        return self.care_visit_repo.get_care_visits(
            start_date=start_date,
            end_date=end_date,
            patient_id=patient_id
        )

    def save_care_visit(self, care_visit: CareVisit):
        return self.care_visit_repo.save(care_visit)

    def schedule_care_visit(self, patient_id: str, employee_id: str, visit_date: datetime,
                            scheduled_start_time: datetime, scheduled_end_time: datetime,
                            scheduled_by_id: str, availability_slot_id: str, patient_care_slot_id: str,
                            organization_id: str):

        care_visit = CareVisit(
            status=CareVisitStatusEnum.SCHEDULED,
            patient_id=patient_id,
            employee_id=employee_id,
            visit_date=visit_date,
            scheduled_start_time=scheduled_start_time,
            scheduled_end_time=scheduled_end_time,
            scheduled_by_id=scheduled_by_id,
            availability_slot_id=availability_slot_id,
            patient_care_slot_id=patient_care_slot_id,
            organization_id=organization_id
        )
        return self.save_care_visit(care_visit)

    def schedule_multiple_care_visits(self, visits_data: List[Dict[str, Any]], scheduled_by_id: str,
                                      organization_id: str) -> List[CareVisit]:
        """
        Schedule multiple care visits from a list of visit data.
        """
        scheduled_visits = []

        for visit_data in visits_data:
            # Parse datetime fields
            visit_date = datetime.fromisoformat(visit_data['visit_date'].replace('Z', ''))
            scheduled_start_time = datetime.fromisoformat(visit_data['scheduled_start_time'].replace('Z', ''))
            scheduled_end_time = datetime.fromisoformat(visit_data['scheduled_end_time'].replace('Z', ''))

            care_visit = self.schedule_care_visit(
                patient_id=visit_data['patient_id'],
                employee_id=visit_data['employee_id'],
                visit_date=visit_date,
                scheduled_start_time=scheduled_start_time,
                scheduled_end_time=scheduled_end_time,
                scheduled_by_id=scheduled_by_id,
                availability_slot_id=visit_data['availability_slot_id'],
                patient_care_slot_id=visit_data['patient_care_slot_id'],
                organization_id=organization_id
            )
            scheduled_visits.append(care_visit)

        return scheduled_visits

    def get_care_visit_by_id(self, care_visit_id: str) -> CareVisit:
        return self.care_visit_repo.get_one({"entity_id": care_visit_id})

    def process_missed_visits(self, employee_id=None, current_datetime=None) -> int:
        care_visits = self.care_visit_repo.get_care_visits(
            employee_id=employee_id
        )

        count = 0
        for visit_data in care_visits:
            if (visit_data.get('status') == CareVisitStatusEnum.SCHEDULED and
                    visit_data.get('scheduled_end_time') and
                    visit_data['scheduled_end_time'] < current_datetime):

                care_visit = self.get_care_visit_by_id(visit_data['entity_id'])
                if care_visit:
                    care_visit.status = CareVisitStatusEnum.MISSED
                    self.save_care_visit(care_visit)
                    count += 1

        return count

    def create_care_visit_from_assignment(self, visit_data: Dict[str, Any]) -> CareVisit:
        """
        Create a care visit from employee assignment data.
        """
        from datetime import datetime, date, time
      
        # Parse date and time fields
        visit_date = datetime.strptime(visit_data['visit_date'], '%Y-%m-%d').date()
        
        # Parse time strings (format: HH:MM)
        start_time_str = visit_data['scheduled_start_time']
        end_time_str = visit_data['scheduled_end_time']
        patient_care_slot_id = visit_data['patient_care_slot_id']
        availability_slot_id = visit_data['availability_slot_id']
        
        # Convert time strings to datetime objects for the visit date
        start_time = datetime.strptime(f"{visit_date} {start_time_str}", '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(f"{visit_date} {end_time_str}", '%Y-%m-%d %H:%M')
        
        # Convert visit_date to datetime (start of day) since the model expects datetime
        visit_datetime = datetime.combine(visit_date, datetime.min.time())
        
        # Create the care visit
        care_visit = CareVisit(
            status=CareVisitStatusEnum.SCHEDULED,
            patient_id=visit_data['patient_id'],
            employee_id=visit_data['employee_id'],
            visit_date=visit_datetime,  # Use datetime instead of date
            scheduled_start_time=start_time,
            scheduled_end_time=end_time,
            scheduled_by_id=visit_data['scheduled_by_id'],
            availability_slot_id=visit_data.get('availability_slot_id', ''),
            patient_care_slot_id=visit_data.get('patient_care_slot_id', ''),
            organization_id=visit_data['organization_id']
        )
        
        return self.save_care_visit(care_visit)

    def assign_employee_to_recurring_pattern(self, visit_data: Dict[str, Any]) -> List[CareVisit]:
        """
        Assign an employee to ALL slots in a recurring pattern using series_id.
        """
        from common.services import PatientCareSlotService, AvailabilitySlotService
        from common.models.availability_slot import AvailabilitySlot
        
        series_id = visit_data.get('series_id')
        patient_id = visit_data.get('patient_id')
        patient_slot_id = visit_data.get('patient_slot_id')
        
        if not patient_id:
            raise ValueError(" patient_id is required for recurring assignment")
      
        
        # Find all patient care slots with this series_id
        patient_care_slot_service = PatientCareSlotService(self.config)
        all_slots = patient_care_slot_service.get_slots_by_series_id(
            series_id, 
            patient_slot_id,
            patient_id
        )
        if not all_slots:
            raise ValueError(f"No active slots found for series_id: {series_id}")
        
        created_visits = []

        availability_slot_service = AvailabilitySlotService(self.config)

        for slot in all_slots:
            # Create a matching availability slot for the employee for this occurrence 
            availability_slot = AvailabilitySlot(
                employee_id=visit_data['employee_id'],
                start_day_of_week=slot.start_day_of_week,
                end_day_of_week=slot.end_day_of_week,
                start_time=slot.start_time,
                end_time=slot.end_time,
                start_date=slot.start_date,
                end_date=slot.end_date,
                series_id = slot.series_id
            )
            
            saved_availability_slot = availability_slot_service.save_availability_slot(availability_slot)

           
            slot_visit_data = {
                **visit_data,
                'visit_date': slot.start_date.strftime('%Y-%m-%d'),
                'scheduled_start_time': slot.start_time.strftime('%H:%M'), 
                'scheduled_end_time': slot.end_time.strftime('%H:%M'),
                'patient_care_slot_id': getattr(slot, 'entity_id', ''),
                'availability_slot_id': getattr(saved_availability_slot, 'entity_id', ''),
            }
            care_visit = self.create_care_visit_from_assignment(slot_visit_data)
            created_visits.append(care_visit)
        return created_visits
    