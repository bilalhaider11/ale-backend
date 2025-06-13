from typing import Optional, List
from datetime import date

from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.oig_exclusions_check import OigExclusionsCheck

logger = get_logger(__name__)


class OigExclusionsCheckService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.oig_checks_repo = self.repository_factory.get_repository(RepoType.OIG_EXCLUSIONS_CHECK, message_queue_name="")
    
    def get_last_successful_import_date(self) -> Optional[date]:
        """Get the last successful import date from oig_exclusions_check table"""
        try:
            # Get all records with status 'imported', ordered by created_at desc
            successful_imports = self.oig_checks_repo.get_checks_by_status('imported')
            if successful_imports:
                # Sort by changed_on descending and get the first one
                successful_imports.sort(key=lambda x: x.changed_on, reverse=True)
                return successful_imports[0].last_update_on_webpage
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting last successful import date: {str(e)}")
            return None
    
    def log_check_result(self, status: str, last_update_on_webpage: Optional[date] = None) -> bool:
        """Log the check result to oig_exclusions_check table"""
        try:
            check_record = OigExclusionsCheck(
                status=status,
                last_update_on_webpage=last_update_on_webpage
            )
            
            # Use repository method to save the check record
            self.oig_checks_repo.save(check_record)
            logger.info(f"Logged check result with status: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging check result: {str(e)}")
            return False
    
    def get_all_checks(self) -> List[OigExclusionsCheck]:
        """Get all OIG exclusion checks"""
        try:
            return self.oig_checks_repo.get_all_checks()
        except Exception as e:
            logger.error(f"Error retrieving OIG exclusion checks: {str(e)}")
            raise
    
    def get_checks_by_status(self, status: str) -> List[OigExclusionsCheck]:
        """Get OIG exclusion checks by status"""
        try:
            return self.oig_checks_repo.get_checks_by_status(status)
        except Exception as e:
            logger.error(f"Error retrieving OIG exclusion checks by status {status}: {str(e)}")
            raise
