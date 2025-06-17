from typing import Optional, List
from datetime import date

from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.employee_exclusion_match import EmployeeExclusionMatch

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
