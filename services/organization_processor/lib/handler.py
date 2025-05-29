from common.app_logger import create_logger
from common.app_config import config
from lib.route53_handler import process_subdomain
from lib.s3_handler import process_logo

logger = create_logger()

def process_organization_message(message):
    """
    Process organization messages
    
    Args:
        message: Dictionary containing organization data and action
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Processing organization message")
    
    action = message.get('action')
    organization_id = message.get('organization_id')
    data = message.get('data', {})
    
    if not organization_id:
        logger.error("No organization_id in message")
        return False
    
    # Get the organization
    try:
        # Import here to avoid circular imports
        from common.services.organization import OrganizationService
        
        organization_service = OrganizationService(config)
        organization = organization_service.get_organization_by_id(organization_id)
        
        if not organization:
            logger.error(f"Organization not found: {organization_id}")
            return False
        
        if action == 'update':
            success = True
            
            # Process logo if present
            if 'logo_url' in data and data['logo_url']:
                logo_success = process_logo(organization, data['logo_url'])
                success = success and logo_success
            
            # Process subdomain if present
            if 'subdomain' in data and data['subdomain']:
                subdomain_success = process_subdomain(organization, data['subdomain'])
                success = success and subdomain_success
                
            return success
        else:
            logger.warning(f"Unknown action: {action}")
            return False
    except Exception as e:
        logger.exception(f"Error in process_organization_message: {e}")
        return False
