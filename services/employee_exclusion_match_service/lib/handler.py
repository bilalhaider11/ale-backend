from common.app_logger import logger
from common.app_config import config
from common.repositories.factory import RepositoryFactory, RepoType
from common.services.s3_client import S3ClientService

def message_handler(message):
    """
    Handle incoming messages for employee exclusion match processing
    """
    logger.info("Processing employee exclusion match message: %s", message)

    s3_client = S3ClientService()
    s3_key = None
    organization_id = None
    if message['source'] == 'csv_import_handler' and 'key' in message:
        s3_key = message['key']
        organization_id = s3_key.split('/')[-2]
        s3_client.update_tags(s3_key, {"status": "matching"})

    if organization_id:
        logger.info("Running employee exclusion match service for organization: %s", organization_id)
    else:
        logger.info("Running employee exclusion match service for all organizations.")

    # Get the repository
    repository_factory = RepositoryFactory(config)
    employee_exclusion_match_repo = repository_factory.get_repository(repo_type=RepoType.EMPLOYEE_EXCLUSION_MATCH)
    
    # Find exclusion matches
    matches = employee_exclusion_match_repo.find_exclusion_matches(organization_id=organization_id)
    logger.info("Found %d exclusion matches", len(matches))
    
    # Update the matches in the database
    employee_exclusion_match_repo.upsert_matches(matches)
    logger.info("Successfully updated employee exclusion matches")

    if s3_key is not None:
        s3_client.update_tags(s3_key, {"status": "done"})
