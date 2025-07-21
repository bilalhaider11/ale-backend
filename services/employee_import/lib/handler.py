from common.app_logger import create_logger
from .employee_handler import EmployeeHandler
from common.tasks.send_message import send_message
from common.app_config import config


logger = create_logger()

class ListImportHandler:
    """Main handler that routes CSV and XLSX imports based on S3 key prefix"""
    
    def __init__(self, config):
        self.config = config
        self.employee_handler = EmployeeHandler(config)
        self.employees_prefix = f"{config.AWS_S3_KEY_PREFIX}employees-list/"
        self.physicians_prefix = f"{config.AWS_S3_KEY_PREFIX}physicians-list/"
        
    def process_list_file(self, bucket, key):
        """
        Process a CSV or XLSX file based on its prefix
        
        Args:
            bucket (str): S3 bucket name
            key (str): S3 object key
            
        Returns:
            bool: True if successful, False otherwise
        """
        if key.startswith(self.employees_prefix):
            logger.info(f"Processing employee list file: {bucket}/{key}")
            import_success = self.employee_handler.process_employee_list(key, "employee")
            if import_success:
                self.trigger_match_service(key)
        elif key.startswith(self.physicians_prefix):
            logger.info(f"Processing physician list file: {bucket}/{key}")
            import_success = self.employee_handler.process_employee_list(key, "physician")
            if import_success:
                self.trigger_match_service(key)
        else:
            logger.info(f"Unknown prefix for list file: {key}")


    def trigger_match_service(self, s3_key):
        """
        Trigger the matching process for employees and caregivers
        """
        logger.info("Triggering matching process for employees and caregivers")
        logger.info("Sending message to queue: %s",
            self.config.PREFIXED_EMPLOYEE_EXCLUSION_MATCH_PROCESSOR_QUEUE_NAME
        )
        send_message(
            queue_name=self.config.PREFIXED_EMPLOYEE_EXCLUSION_MATCH_PROCESSOR_QUEUE_NAME,
            data={
                'action': 'match_exclusions',
                'source': 'csv_import_handler',
                'key': s3_key
            }
        )
        logger.info("Matching process triggered in exclusion match service")
