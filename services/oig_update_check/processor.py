from datetime import datetime, timezone 
from common.app_logger import create_logger, set_rollbar_exception_catch
from common.app_config import config
from lib.handler import task_handler

class OigUpdateCheckProcessor:
    """
    Service processor that checks for OIG LEIE database updates
    """
    def __init__(self):
        set_rollbar_exception_catch()
        self.logger = create_logger()
        # Initialize any other resources needed for the processor

    def process(self):
        """Main processor loop"""
        # Use the recommended timezone-aware method for UTC time
        try:
            self.logger.info("OIG update check processor execution started at %s ...", datetime.now(timezone.utc))
            
            # Check for OIG LEIE database updates
            task_handler()
            
            self.logger.info("OIG update check processor execution finished at %s ...", datetime.now(timezone.utc))
        except Exception as e:
            self.logger.error(f"Error in OIG update check processor: {str(e)}")
            self.logger.exception(e)
