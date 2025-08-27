from common.app_logger import logger
from common.app_config import config
from common.repositories.factory import RepositoryFactory, RepoType
from common.services.s3_client import S3ClientService
from common.models.current_employees_file import CurrentEmployeesFileStatusEnum
from common.services.current_employees_file import CurrentEmployeesFileService
from common.tasks.send_message import send_message

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

        # Send matches to OIG verifier service if matches found
        if matches:
            trigger_oig_verifier(matches)

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

        # Send matches to OIG verifier service if matches found
        if matches:
            trigger_oig_verifier(matches)


def trigger_oig_verifier(matches):
    """
    Send matches to the OIG verifier service for processing
    
    Args:
        matches: List of EmployeeExclusionMatch objects
    """
    if not matches:
        return
    
    logger.info("Sending %d matches to OIG verifier service", len(matches))
    
    # Convert matches to message format
    matches_data = []
    for match in matches:
        match_data = {
            'entity_id': match.entity_id,
            'matched_entity_id': match.matched_entity_id,
            'matched_entity_type': match.matched_entity_type,
            'organization_id': match.organization_id,
            'first_name': match.first_name,
            'last_name': match.last_name,
            'date_of_birth': match.date_of_birth.isoformat() if match.date_of_birth else None,
            'match_type': match.match_type,
            'exclusion_type': match.exclusion_type,
            'exclusion_date': match.exclusion_date.isoformat() if match.exclusion_date else None
        }
        matches_data.append(match_data)
    
    # Send message to OIG verifier queue
    message = {
        'action': 'verify_matches',
        'source': 'employee_exclusion_match_service',
        'matches': matches_data
    }
    
    try:
        send_message(
            queue_name=config.PREFIXED_OIG_VERIFIER_QUEUE_NAME,
            data=message
        )
        logger.info("Successfully sent matches to OIG verifier service")
    except Exception as e:
        logger.error("Failed to send matches to OIG verifier service: %s", str(e))
        logger.exception(e)
