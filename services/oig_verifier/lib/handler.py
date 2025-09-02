import os
import time
from datetime import datetime
from common.app_logger import logger
from common.app_config import config
from common.repositories.factory import RepositoryFactory, RepoType
from common.services.employee_exclusion_match import EmployeeExclusionMatchService
from common.services.pusher_client import PusherService
from common.models.employee_exclusion_match import EmployeeExclusionMatch
from lib.oig_verification_script import OIGVerifier

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
    employee_repo = repository_factory.get_repository(repo_type=RepoType.EMPLOYEE)

    # Mark all matches as in_process before starting verification
    for match_data in matches_data:
        try:
            match_id = match_data.get('entity_id')
            match = employee_exclusion_match_repo.get_one({"entity_id": match_id})
            if match:
                match.verification_result = 'in_process'
                match.s3_key = None  # Clear verification screenshot when setting to in_process
                employee_exclusion_match_repo.save(match)
                logger.info(f"Marked match {match_id} as in_process and cleared verification screenshot")
        except Exception as e:
            logger.error(f"Error marking match {match_data.get('entity_id')} as in_process: {str(e)}")

    # Process each match
    for match_data in matches_data:
        try:
            verify_match(match_data, employee_exclusion_match_repo, employee_exclusion_match_service, employee_repo)
        except Exception as e:
            logger.error(f"Error verifying match {match_data.get('entity_id')}: {str(e)}")
            logger.exception(e)

def verify_match(match_data, employee_exclusion_match_repo, employee_exclusion_match_service, employee_repo):
    """
    Verify a single exclusion match using the OIG verification script
    
    Args:
        match_data: Dictionary containing match information
        employee_exclusion_match_repo: Repository for employee exclusion matches
        employee_exclusion_match_service: Service for employee exclusion matches
        employee_repo: Repository for employee data
    """
    match_id = match_data.get('entity_id')
    matched_entity_id = match_data.get('matched_entity_id')
    matched_entity_type = match_data.get('matched_entity_type')
    organization_id = match_data.get('organization_id')
    match_type = match_data.get('match_type')
    first_name = match_data.get('first_name')
    last_name = match_data.get('last_name')
    
    logger.info(f"Verifying match {match_id} for {matched_entity_type} {matched_entity_id}")

    # Get the match record from database
    match = employee_exclusion_match_repo.get_one({"entity_id": match_id})
    if not match:
        logger.error(f"Match record not found for ID: {match_id}")
        return

    # Get employee data to retrieve SSN
    if matched_entity_type == 'employee':
        employee = employee_repo.get_one({"entity_id": matched_entity_id})
        if not employee:
            logger.error(f"Employee record not found for ID: {matched_entity_id}")
            return
        
        ssn = employee.social_security_number
        if not ssn:
            logger.warning(f"No SSN found for employee {matched_entity_id}, skipping OIG verification")
            verification_result = {
                'status': 'skipped',
                'result': 'No SSN',
                'notes': f"Employee {first_name} {last_name} has no SSN on file",
                'verified_on': datetime.utcnow().isoformat()
            }
        else:
            # Perform OIG verification using the scraping script
            verification_result = perform_oig_verification(first_name, last_name, ssn, employee.organization_id, employee.person_id)
    else:
        logger.warning(f"Verification not implemented for entity type: {matched_entity_type}")
        verification_result = {
            'status': 'skipped',
            'result': 'Not Implemented',
            'notes': f"Verification not implemented for entity type: {matched_entity_type}",
            'verified_on': datetime.utcnow().isoformat()
        }

    # Skip database update for now - just log the results
    update_match_verification_status(match, verification_result, employee_exclusion_match_repo)
    
    # Log verification result
    logger.info(f"Verification completed for match {match_id}: {verification_result}")
    logger.info(f"Screenshots and verification details available for audit")

def perform_oig_verification(first_name, last_name, ssn, organization_id, person_id):
    """
    Perform the actual OIG verification using the scraping script
    
    Args:
        first_name (str): First name
        last_name (str): Last name
        ssn (str): Social Security Number
        
    Returns:
        dict: Verification result with status and details
    """
    logger.info(f"Starting OIG verification for {first_name} {last_name} with SSN {ssn[-4:].rjust(len(ssn), '*')}")
    
    verifier = None
    try:
        # Clean SSN (remove any dashes or spaces)
        clean_ssn = ssn.replace('-', '').replace(' ', '') if ssn else None
        
        if not clean_ssn or len(clean_ssn) != 9:
            logger.error(f"Invalid SSN format for {first_name} {last_name}")
            return {
                'status': 'error',
                'result': 'Invalid SSN',
                'notes': f"SSN format is invalid: {ssn}",
                'verified_on': datetime.utcnow().isoformat()
            }

        # Initialize the OIG verifier
        verifier = OIGVerifier()
        
        # Perform verification
        verification_response = verifier.verify_person(first_name, last_name, clean_ssn, organization_id, person_id)
        
        # Extract result and S3 key from response
        result = verification_response.get('result', 'Error')
        s3_key = verification_response.get('s3_key')
        
        # Parse the result
        if result == "Match":
            status = 'verified'
            oig_result = 'Match'
            notes = f"OIG verification successful - Match confirmed for {first_name} {last_name}"
        elif result == "NoMatch":
            status = 'verified'
            oig_result = 'NoMatch'
            notes = f"OIG verification completed - No match found for {first_name} {last_name}"
        elif result == "NoSearch":
            status = 'verified'
            oig_result = 'NoSearch'
            notes = f"OIG verification completed - No search results found for {first_name} {last_name}"
        else:
            status = 'error'
            oig_result = 'Error'
            notes = f"OIG verification failed with error: {result}"
        
        verification_result = {
            'status': status,
            'result': oig_result,
            'notes': notes,
            'verified_on': datetime.utcnow().isoformat(),
            'raw_result': result,
            's3_key': s3_key
        }
        
        logger.info(f"OIG verification completed for {first_name} {last_name}: {oig_result}")
        return verification_result
        
    except Exception as e:
        logger.error(f"Error during OIG verification for {first_name} {last_name}: {str(e)}")
        logger.exception(e)
        
        return {
            'status': 'error',
            'result': 'Error',
            'notes': f"OIG verification failed with exception: {str(e)}",
            'verified_on': datetime.utcnow().isoformat(),
            'error': str(e)
        }
    finally:
        # Clean up the verifier
        if verifier:
            try:
                verifier.close()
            except Exception as cleanup_error:
                logger.warning(f"Error closing verifier: {cleanup_error}")

def update_match_verification_status(match, verification_result, employee_exclusion_match_repo):
    """
    Update the match record with verification results
    
    Args:
        match: EmployeeExclusionMatch object
        verification_result: Dictionary containing verification results
        employee_exclusion_match_repo: Repository for employee exclusion matches
    """
    try:
        # Store the verification result in the verification_result column
        match.verification_result = verification_result.get('result')
        
        # Add verification details to reviewer notes
        verification_notes = verification_result.get('notes', '')
        verification_time = verification_result.get('verified_on', datetime.utcnow().isoformat())
        
        match.reviewer_notes = f"OIG Verification Result: {verification_result.get('result', 'Unknown')}\n"
        match.reviewer_notes += f"Verified On: {verification_time}\n"
        match.reviewer_notes += f"Notes: {verification_notes}"
        
        match.reviewer_name = "OIG Verifier Service"
        match.review_date = datetime.utcnow().date()
        
        # Save the S3 key if available
        if verification_result.get('s3_key'):
            match.s3_key = verification_result['s3_key']
        
        # Save the updated match
        employee_exclusion_match_repo.save(match)
        
        # Trigger real-time update via Pusher
        try:
            pusher_service = PusherService()
            match_update_data = {
                'entity_id': match.entity_id,
                'matched_entity_id': match.matched_entity_id,
                'verification_result': match.verification_result,
                's3_key': match.s3_key,
                'updated_at': datetime.utcnow().isoformat()
            }
            pusher_service.trigger_verification_update(match.organization_id, match_update_data)
        except Exception as pusher_error:
            logger.warning(f"Failed to send Pusher notification for match {match.entity_id}: {str(pusher_error)}")
        
        logger.info(f"Updated match {match.entity_id} with verification result: {match.verification_result}")
        
    except Exception as e:
        logger.error(f"Error updating match verification status for {match.entity_id}: {str(e)}")
        logger.exception(e)

 