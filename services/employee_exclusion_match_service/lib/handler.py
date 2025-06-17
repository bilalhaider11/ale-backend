from common.app_logger import logger
from common.app_config import config
from common.repositories.factory import RepositoryFactory, RepoType


def message_handler(message):
    """
    Handle incoming messages for employee exclusion match processing
    """
    logger.info("Processing employee exclusion match message: %s", message)
    
    # Get the repository
    repository_factory = RepositoryFactory(config)
    employee_exclusion_match_repo = repository_factory.get_repository(repo_type=RepoType.EMPLOYEE_EXCLUSION_MATCH)
    
    # Find exclusion matches
    matches = employee_exclusion_match_repo.find_exclusion_matches()
    logger.info("Found %d exclusion matches", len(matches))
    
    # Update the matches in the database
    employee_exclusion_match_repo.update_matches(matches)
    logger.info("Successfully updated employee exclusion matches")
