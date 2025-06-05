import json
from rococo.messaging import BaseServiceProcessor
from common.app_config import config
from common.app_logger import create_logger, set_rollbar_exception_catch

class OrganizationProcessor(BaseServiceProcessor):
    """
    Service processor that processes organization updates from SQS messages
    """
    def __init__(self):
        super().__init__()
        self.logger = create_logger()
        set_rollbar_exception_catch()
        
        # Set up the queue infrastructure
        from setup import setup_organization_processor_queue
        setup_organization_processor_queue()
        
        self.logger.info("Organization processor initialized")
        
    def process(self, message):
        """Main processor method that handles incoming messages"""
        try:
            self.logger.info(f"Processing organization message:")
            
            if not isinstance(message, dict):
                self.logger.warning(f"Received non-dict message: {type(message)}")
                return False
                
            # Handle different message types
            if "action" in message and message["action"] == "organization_updated":
                org_id = message.get('organization_id')
                org_data = message.get('organization_data', {})
                
                if not org_id:
                    self.logger.error("No organization_id in message")
                    return False
                
                # Get the organization
                from common.services.organization import OrganizationService
                from lib.s3_handler import process_logo
                from lib.route53_handler import process_subdomain
                
                organization_service = OrganizationService(config)
                organization = organization_service.get_organization_by_id(org_id)
                
                if not organization:
                    self.logger.error(f"Organization not found: {org_id}")
                    return False
                
                success = True
                
                # Process logo if present
                if 'logo_data' in org_data and org_data['logo_data']:
                    logo_success = process_logo(organization, org_data['logo_data'])
                    success = success and logo_success
                    self.logger.info(f"Logo processing result: {logo_success}")
                
                # Process subdomain if present
                if 'subdomain' in org_data and org_data['subdomain']:
                    subdomain_success = process_subdomain(organization, org_data['subdomain'])
                    success = success and subdomain_success
                    self.logger.info(f"Subdomain processing result: {subdomain_success}")
                    
                return success
                
            else:
                self.logger.warning(f"Unknown message format: {message}")
                return False
                
        except Exception as e:
            self.logger.exception(f"Error processing organization message: {str(e)}")
            return False
