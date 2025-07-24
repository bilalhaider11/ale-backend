from common.app_logger import logger
from common.app_config import config
from common.repositories.factory import RepositoryFactory, RepoType
from common.services.s3_client import S3ClientService
from common.models.current_employees_file import CurrentEmployeesFileStatusEnum
from common.services.current_employees_file import CurrentEmployeesFileService

def message_handler(message):
    """
    Handle incoming messages for employee exclusion match processing
    """
    logger.info("Processing employee exclusion match message: %s", message)

    employees_file_service = CurrentEmployeesFileService(config)
    s3_key = None
    organization_id = None
    employees_file = None
    
    if message['source'] == 'csv_import_handler' and 'key' in message:
        logger.info("Received CSV import message: %s", message)
        s3_key = message['key']
        _, organization_id, file_id = s3_key.rsplit('/', 2)
        employees_file = employees_file_service.get_by_id(file_id, organization_id)
        employees_file_service.update_status(employees_file, CurrentEmployeesFileStatusEnum.MATCHING)

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

        if employees_file is not None:
            # Update the employees file status to done
            employees_file_service.update_status(employees_file, CurrentEmployeesFileStatusEnum.DONE)
            logger.info("Updated employees file status to done: %s", employees_file.entity_id)

    elif message['source'] == 'employee_creation':
        logger.info("Received employee creation message: %s", message)
        employee_id = message.get('employee_id')

        logger.info("Running employee exclusion match service for employee: %s", employee_id)
        
        # Get the repository
        repository_factory = RepositoryFactory(config)
        employee_exclusion_match_repo = repository_factory.get_repository(repo_type=RepoType.EMPLOYEE_EXCLUSION_MATCH)

        # Find exclusion matches
        matches = employee_exclusion_match_repo.find_exclusion_matches_for_employee(employee_id=employee_id)
        logger.info("Found %d exclusion matches for employee: %s", len(matches), employee_id)

        # Update the matches in the database
        employee_exclusion_match_repo.upsert_matches(matches)
        logger.info("Successfully updated employee exclusion matches for employee: %s", employee_id)
