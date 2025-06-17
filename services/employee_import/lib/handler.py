from common.app_logger import create_logger
from .current_employee_handler import CurrentEmployeeHandler
from .current_caregiver_handler import CurrentCaregiverHandler
from common.tasks.send_message import send_message
from common.app_config import config


logger = create_logger()

class CsvImportHandler:
    """Main handler that routes CSV imports based on S3 key prefix"""
    
    def __init__(self, config):
        self.config = config
        self.employee_handler = CurrentEmployeeHandler(config)
        self.caregiver_handler = CurrentCaregiverHandler(config)
        
    def process_csv_file(self, bucket, key):
        """
        Process a CSV file based on its prefix
        
        Args:
            bucket (str): S3 bucket name
            key (str): S3 object key
            
        Returns:
            bool: True if successful, False otherwise
        """
        if key.startswith('employees-list/') and not key.endswith('latest.csv'):
            logger.info(f"Processing employee CSV: {bucket}/{key}")
            self.employee_handler.process_employee_csv(bucket, key)
            self.trigger_match_service()

        elif key.startswith('caregivers-list/') and not key.endswith('latest.csv'):
            logger.info(f"Processing caregiver CSV: {bucket}/{key}")
            self.caregiver_handler.process_caregiver_csv(bucket, key)
            self.trigger_match_service()

        else:
            if key.endswith('latest.csv'):
                logger.info(f"Skipping latest CSV file: {key}")
            else:
                logger.warning(f"Unknown prefix for CSV file: {key}")
                return False

    def trigger_match_service(self):
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
                'source': 'csv_import_handler'
            }
        )
        logger.info("Matching process triggered in exclusion match service")
