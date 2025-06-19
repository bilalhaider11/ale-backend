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
        from setup import setup_organization_processor_queue, setup_s3_to_sqs_notification_for_logos
        setup_organization_processor_queue()
        setup_s3_to_sqs_notification_for_logos()
        
        self.logger.info("Organization processor initialized")
        
    def process(self, message):
        """Main processor method that handles incoming messages"""
        try:
            self.logger.info("Processing organization message")
            
            if not isinstance(message, dict):
                self.logger.warning(f"Received non-dict message: {type(message)}")
                return False
            
            # Handle S3 event messages (logo uploads)
            if "Records" in message:
                self.logger.info("Received S3 event message")
                from lib.s3_handler import process_s3_event
                return process_s3_event(message)
                
            # Handle direct organization update messages (subdomain processing)
            if "action" in message and message["action"] == "organization_updated":
                self.logger.info("Received organization update message")
                from lib.route53_handler import process_subdomain
                
                # Process subdomain if present
                if "subdomain" in message.get("organization_data", {}):
                    organization_id = message["organization_id"]
                    subdomain = message["organization_data"]["subdomain"]
                    return process_subdomain(organization_id, subdomain)
                
                return True
                
            else:
                self.logger.info(f"Unknown message format: {message}")
                return False
                
        except Exception as e:
            self.logger.exception(f"Error processing organization message: {str(e)}")
            return False
