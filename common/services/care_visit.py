from typing import List
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

    def save_care_visit(self, care_visit: CareVisit):
        return self.care_visit_repo.save(care_visit)

    def schedule_care_visit(self, patient_id: str, employee_id: str, visit_date: datetime, 
                           scheduled_start_time: datetime, scheduled_end_time: datetime, 
                           scheduled_by_id: str, availability_slot_id: str, organization_id: str):
        care_visit = CareVisit(
            status=CareVisitStatusEnum.SCHEDULED,
            patient_id=patient_id,
            employee_id=employee_id,
            visit_date=visit_date,
            scheduled_start_time=scheduled_start_time,
            scheduled_end_time=scheduled_end_time,
            scheduled_by_id=scheduled_by_id,
            availability_slot_id=availability_slot_id,
            organization_id=organization_id
        )
        return self.save_care_visit(care_visit)
