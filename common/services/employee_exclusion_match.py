from typing import Optional, List
from datetime import datetime

from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.employee_exclusion_match import EmployeeExclusionMatch
from common.models.person import Person
from common.helpers.exceptions import APIException

logger = get_logger(__name__)


class EmployeeExclusionMatchService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.employee_exclusion_match_repo = self.repository_factory.get_repository(RepoType.EMPLOYEE_EXCLUSION_MATCH)

    def get_all_matches(self) -> List[EmployeeExclusionMatch]:
        """Get all employee exclusion matches"""
        return [
            match.as_dict() for match in self.employee_exclusion_match_repo.get_all()
        ]

    def update_exclusion_match(self, entity_id: str, reviewer: Person, reviewer_notes: str=None, status: str=None):
        match = self.employee_exclusion_match_repo.get_one({"entity_id": entity_id})
        if not match:
            raise APIException("Match object not found")
        
        should_save = False

        if status and status != match.status:
            should_save = True
        
        if reviewer_notes and reviewer_notes != match.reviewer_notes:
            should_save = True
        
        if should_save:
            if match.reviewer_id != reviewer.entity_id:
                match.reviewer_id = reviewer.entity_id
                match.reviewer_name = (reviewer.first_name if reviewer.first_name else '') + ' ' + (reviewer.last_name if reviewer.last_name else '').strip()
                match.review_date = datetime.now()
            match.status = status if status else match.status
            match.reviewer_notes = reviewer_notes if reviewer_notes else match.reviewer_notes
            return self.employee_exclusion_match_repo.save(match)
        else:
            return match

    def get_match_by_entity_id(self, entity_id: str) -> Optional[EmployeeExclusionMatch]:
        """Get an exclusion match object by entity_id"""
        match = self.employee_exclusion_match_repo.get_one({"entity_id": entity_id})
        if not match:
            raise APIException("Match object not found")
        
        return match
