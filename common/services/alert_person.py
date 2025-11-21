from typing import List, Optional
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.alert_person import AlertPerson
from common.tasks.send_message import send_message
class AlertPersonService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.alert_person_repo = self.repository_factory.get_repository(RepoType.ALERT_PERSON)
        self.alert_repo = self.repository_factory.get_repository(RepoType.ALERT)
        self.person_repo = self.repository_factory.get_repository(RepoType.PERSON)
    
    def save_alert_person(self, alert_person: AlertPerson) -> AlertPerson:
        return self.alert_person_repo.save(alert_person)
    
    def get_alert_person_by_id(self, entity_id: str) -> Optional[AlertPerson]:
        return self.alert_person_repo.get_one({"entity_id": entity_id})
    
    def get_alert_persons_by_person(self, person_id: str) -> List[AlertPerson]:
        return self.alert_person_repo.get_many({"person_id": person_id})
    
    def get_alert_persons_by_alert(self, alert_id: str) -> List[AlertPerson]:
        return self.alert_person_repo.get_many({"alert_id": alert_id})
    
    def get_alert_person_by_alert_and_person(self, alert_id: str, person_id: str) -> Optional[AlertPerson]:
        return self.alert_person_repo.get_one({"alert_id": alert_id, "person_id": person_id})
    
    def mark_read(self,  alert_id: str, person_id: str):
        #send message here rabbit mq
        return

    def mark_alert_as_read(self, alert_id: str, person_id: str) -> AlertPerson:
        alert_person = self.get_alert_person_by_alert_and_person(alert_id, person_id)
        if not alert_person:
            alert_person = AlertPerson(
                alert_id=alert_id,
                person_id=person_id,
                read=True,
            )
            return self.save_alert_person(alert_person)
        
        alert_person.read = True
        return self.save_alert_person(alert_person)

    def create_alert_person(self, alert_id: str, person_id: str, read: bool = False) -> AlertPerson:
        existing = self.get_alert_person_by_alert_and_person(alert_id, person_id)
        if existing:
            return existing
        
        alert_person = AlertPerson(
            alert_id=alert_id,
            person_id=person_id,
            read=read,
        )
        return self.save_alert_person(alert_person)
    
    def assign_alert_to_persons(self, alert_id: str, person_ids: List[str]) -> List[AlertPerson]:
        results = []
        for person_id in person_ids:
            alert_person = self.create_alert_person(alert_id, person_id)
            results.append(alert_person)
        return results
    
    def get_unread_alerts_for_person(self, person_id: str) -> List[AlertPerson]:
        relationships = self.get_alert_persons_by_person(person_id)
        return [r for r in relationships if not r.read]
