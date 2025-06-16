from common.app_logger import create_logger
from .current_employee_handler import CurrentEmployeeHandler
from .current_caregiver_handler import CurrentCaregiverHandler

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
        if key.startswith('employees-list/'):
            logger.info(f"Processing employee CSV: {bucket}/{key}")
            return self.employee_handler.process_employee_csv(bucket, key)
        elif key.startswith('caregivers-list/'):
            logger.info(f"Processing caregiver CSV: {bucket}/{key}")
            return self.caregiver_handler.process_caregiver_csv(bucket, key)
        else:
            logger.warning(f"Unknown prefix for CSV file: {key}")
            return False
