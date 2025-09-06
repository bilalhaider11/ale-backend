from typing import List, Optional

from common.repositories.factory import RepositoryFactory, RepoType
from common.models.alert import Alert, AlertStatusEnum
from common.models.alert_person import AlertPerson

from datetime import datetime

class AlertService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.alert_repo = self.repository_factory.get_repository(RepoType.ALERT)
        self.alert_person_repo = self.repository_factory.get_repository(RepoType.ALERT_PERSON)
        self.person_repo = self.repository_factory.get_repository(RepoType.PERSON)
    
    def save_alert(self, alert: Alert) -> Alert:
        return self.alert_repo.save(alert)
    
    def get_alert_by_id(self, entity_id: str) -> Optional[Alert]:
        return self.alert_repo.get_one({"entity_id": entity_id})
    
    def get_alerts_by_organization(self, organization_id: str) -> List[Alert]:
        return self.alert_repo.get_many({"organization_id": organization_id})
    
    def get_open_alerts(self, organization_id: str) -> List[Alert]:
        return self.alert_repo.get_many({
                "organization_id": organization_id,
                "status": AlertStatusEnum.OPEN
            })
    
    def get_alerts_by_assigned_to(self, person_id: str) -> List[Alert]:
        return self.alert_repo.get_many({"assigned_to_id": person_id})
    
    def update_alert_status(self, entity_id: str, status: AlertStatusEnum, assigned_to_id: Optional[str] = None) -> Alert:
        alert = self.get_alert_by_id(entity_id)
        if alert:
            alert.status = status
            if assigned_to_id:
                alert.assigned_to_id = assigned_to_id

            now = datetime.now()
            if status == AlertStatusEnum.IN_PROGRESS and alert.status == AlertStatusEnum.OPEN:
                alert.handled_at_start = now
            elif status == AlertStatusEnum.ADDRESSED:
                alert.handled_at_end = now
            return self.save_alert(alert)
    
    def create_alert(self, 
                     organization_id: str, 
                     title: str, 
                     description: str, 
                     status: AlertStatusEnum = AlertStatusEnum.OPEN,
                     alert_type: Optional[str] = None,
                     assigned_to_id: Optional[str] = None) -> Alert:

        alert = Alert(
            organization_id=organization_id,
            area=title,
            message=description,
            level=alert_type,
            status=status,
            assigned_to_id=assigned_to_id,
        )
        return self.save_alert(alert)
        
    def update_alert_fields(self, alert_id: str, updates: dict) -> Optional[Alert]:
        alert = self.get_alert_by_id(alert_id)
        if not alert:
            return None
            
        for field, value in updates.items():
            if hasattr(alert, field):
                setattr(alert, field, value)
                
        return self.save_alert(alert)
