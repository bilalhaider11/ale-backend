from datetime import datetime
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
                           scheduled_by_id: str, availability_slot_key: str, patient_care_slot_key: str, organization_id: str):

        care_visit = CareVisit(
            status=CareVisitStatusEnum.SCHEDULED,
            patient_id=patient_id,
            employee_id=employee_id,
            visit_date=visit_date,
            scheduled_start_time=scheduled_start_time,
            scheduled_end_time=scheduled_end_time,
            scheduled_by_id=scheduled_by_id,
            availability_slot_key=availability_slot_key,
            patient_care_slot_key=patient_care_slot_key,
            organization_id=organization_id
        )
        return self.save_care_visit(care_visit)

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
