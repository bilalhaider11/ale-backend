import json
from rococo.messaging import BaseServiceProcessor
from common.app_config import config
from common.app_logger import create_logger, set_rollbar_exception_catch
from lib.handler import ListImportHandler

class EmployeeImportProcessor(BaseServiceProcessor):
    """
    Service processor that imports employee and caregiver CSV files from S3
    """
    def __init__(self):
        super().__init__()
        self.logger = create_logger()
        set_rollbar_exception_catch()
        
        # Set up the queue infrastructure
        from setup import setup_employee_import_queue
        setup_employee_import_queue()
        
        self.import_handler = ListImportHandler(config)
        
        self.logger.info("Employee import processor initialized")

        self.employees_prefix = f"{config.AWS_S3_KEY_PREFIX}employees-list/"
        
    def process(self, message):
        """Main processor method that handles incoming messages"""
        try:
            self.logger.info("Processing employee import message")
            
            if not isinstance(message, dict):
                try:
                    message = json.loads(message)
                except Exception as e:
                    self.logger.error(f"Failed to parse message as JSON: {str(e)}")
                    return

            # Check if this is an S3 notification
            if 'Records' not in message:
                self.logger.info("Message is not an S3 notification")
                return

            for record in message['Records']:
                if record.get('eventSource') != 'aws:s3':
                    continue
                
                bucket_name = record.get('s3', {}).get('bucket', {}).get('name')
                key = record.get('s3', {}).get('object', {}).get('key')
                
                if not bucket_name or not key:
                    self.logger.warning("Missing bucket name or key in S3 notification")
                    continue

                # Only process files under employees-list/ prefix
                if not key.startswith(self.employees_prefix):
                    self.logger.info(f"Skipping file not under {self.employees_prefix} prefix: {key}")
                    continue
                
                self.logger.info(f"Processing CSV from S3: {bucket_name}/{key}")
                
                # Process the CSV or XLSX file
                self.import_handler.process_list_file(bucket_name, key)

        except Exception as e:
            self.logger.error(f"Error processing employee import message: {str(e)}")
            self.logger.exception(e)
            return False
