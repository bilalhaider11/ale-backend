from common.app_logger import create_logger
from .patient_handler import PatientHandler


logger = create_logger()

class PatientListImportHandler:
    """Main handler that routes CSV and XLSX imports based on S3 key prefix"""
    
    def __init__(self, config):
        self.config = config
        self.patient_handler = PatientHandler(config)
        self.patients_prefix = f"{config.AWS_S3_KEY_PREFIX}patients-list/"
        
    def process_patient_file(self, bucket, key):
        """
        Process a CSV or XLSX file based on its prefix
        
        Args:
            bucket (str): S3 bucket name
            key (str): S3 object key
            
        Returns:
            bool: True if successful, False otherwise
        """
        if key.startswith(self.patients_prefix):
            logger.info(f"Processing patient list file: {bucket}/{key}")
            self.patient_handler.process_patient_list(key)
        else:
            logger.info(f"Unknown prefix for list file: {key}")

