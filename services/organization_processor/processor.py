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
        self.queue_name = config.PREFIXED_ORGANIZATION_PROCESSOR_QUEUE_NAME
        self.logger.info(f"Organization processor initialized with queue: {self.queue_name}")
        
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
                
                # Skip messages with Field objects
                has_field_objects = False
                for key, value in org_data.items():
                    if isinstance(value, str) and "Field(" in value:
                        has_field_objects = True
                        break
                    elif hasattr(value, '__class__') and value.__class__.__name__ == 'Field':
                        has_field_objects = True
                        break
                    
                if has_field_objects:
                    self.logger.warning(f"Skipping message with Field objects: {message}")
                    return True  # Mark as processed so it gets deleted from the queue
                
                # Import the handler here to avoid circular imports
                from lib.handler import process_organization_message
                
                # Create a properly formatted message for the handler
                handler_message = {
                    "organization_id": org_id,
                    "action": "update",
                    "data": {}
                }
                
                # Copy relevant fields to the handler message
                if 'name' in org_data:
                    handler_message['data']['name'] = org_data['name']
                    
                if 'subdomain' in org_data:
                    handler_message['data']['subdomain'] = org_data['subdomain']
                    
                # Handle logo data - could be URL or base64 data
                if 'logo_url' in org_data:
                    handler_message['data']['logo_url'] = org_data['logo_url']
                elif 'logo_data' in org_data:
                    # Pass the entire logo_data dictionary to the handler
                    handler_message['data']['logo_url'] = org_data['logo_data']
                    self.logger.info(f"Found logo_data in message, passing to handler")
                
                # Process the message using the handler
                return process_organization_message(handler_message)
                
            elif "invitation_id" in message:
                self.logger.info(f"Processing invitation: {message['invitation_id']}")
                # Process invitation (placeholder for future implementation)
                return True
                
            else:
                self.logger.warning(f"Unknown message format: {message}")
                return False
                
        except Exception as e:
            self.logger.exception(f"Error processing organization message: {str(e)}")
            return False
