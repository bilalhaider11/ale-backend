from common.app_logger import logger
from common.app_config import config
from common.repositories.factory import RepositoryFactory, RepoType
from common.services.employee_exclusion_match import EmployeeExclusionMatchService
from common.models.employee_exclusion_match import EmployeeExclusionMatch

def message_handler(message):
    """
    Handle incoming messages for OIG verification processing
    """
    logger.info("Processing OIG verification message: %s", message)

    if message.get('action') != 'verify_matches':
        logger.warning("Unknown action received: %s", message.get('action'))
        return

    if message.get('source') != 'employee_exclusion_match_service':
        logger.warning("Unknown source received: %s", message.get('source'))
        return

    matches_data = message.get('matches', [])
    if not matches_data:
        logger.info("No matches to verify")
        return

    logger.info("Processing %d matches for verification", len(matches_data))

    # Initialize services
    repository_factory = RepositoryFactory(config)
    employee_exclusion_match_repo = repository_factory.get_repository(repo_type=RepoType.EMPLOYEE_EXCLUSION_MATCH)
    employee_exclusion_match_service = EmployeeExclusionMatchService(config)

    # Process each match
    for match_data in matches_data:
        try:
            verify_match(match_data, employee_exclusion_match_repo, employee_exclusion_match_service)
        except Exception as e:
            logger.error(f"Error verifying match {match_data.get('entity_id')}: {str(e)}")
            logger.exception(e)

def verify_match(match_data, employee_exclusion_match_repo, employee_exclusion_match_service):
    """
    Verify a single exclusion match
    
    Args:
        match_data: Dictionary containing match information
        employee_exclusion_match_repo: Repository for employee exclusion matches
        employee_exclusion_match_service: Service for employee exclusion matches
    """
    match_id = match_data.get('entity_id')
    matched_entity_id = match_data.get('matched_entity_id')
    matched_entity_type = match_data.get('matched_entity_type')
    organization_id = match_data.get('organization_id')
    match_type = match_data.get('match_type')
    
    logger.info(f"Verifying match {match_id} for {matched_entity_type} {matched_entity_id}")

    # Get the match record from database
    match = employee_exclusion_match_repo.get_one({"entity_id": match_id})
    if not match:
        logger.error(f"Match record not found for ID: {match_id}")
        return

    # Perform verification logic here
    verification_result = perform_verification_logic(match_data)
    
    # Log verification result
    logger.info(f"Verification completed for match {match_id}: {verification_result}")

def perform_verification_logic(match_data):
    """
    Perform the actual verification logic
    
    Args:
        match_data: Dictionary containing match information
        
    Returns:
        dict: Verification result with status and details
    """
    # TODO: Implement your custom verification logic here
    # This is where you would add your business logic for verification
    
    match_type = match_data.get('match_type')
    first_name = match_data.get('first_name')
    last_name = match_data.get('last_name')
    
    # Basic verification result structure
    verification_result = {
        'status': 'verified',
        'notes': f"Match found for {first_name} {last_name} - {match_type} match"
    }
    
    logger.info(f"Verification result: {verification_result}")
    return verification_result

 