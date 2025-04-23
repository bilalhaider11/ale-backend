import sys
import json
import os

from rococo.messaging import BaseServiceProcessor

from common.app_logger import create_logger, set_rollbar_exception_catch
from common.app_config import config

from lib.file_handler import handle_incoming_file
from lib.response_handler import process_textract_message
from setup import setup_textract_notification_channel, setup_s3_to_sqs_notification

class FileProcessor(BaseServiceProcessor):  # pylint: disable=R0903
    """
    Service processor that processes files from SQS messages
    """
    def __init__(self):
        super().__init__()
        self.logger = create_logger()
        set_rollbar_exception_catch()

        setup_textract_notification_channel(
            config.PREFIXED_DOCUMENT_ANALYSIS_RESPONSE_TOPIC_NAME,
            config.PREFIXED_FILE_PROCESSOR_QUEUE_NAME
        )

        setup_s3_to_sqs_notification(
            bucket_name=config.AWS_S3_BUCKET_NAME,
            queue_name=config.PREFIXED_FILE_PROCESSOR_QUEUE_NAME,
            s3_prefix_filter=os.path.join(config.AWS_S3_KEY_PREFIX, 'incoming/')
        )

    def process(self, message):
        """Main processor loop"""
        try:
            self.logger.info("Processing message: %s", message)
            if "s3_key" in message:
                # Received when a message is sent to the queue manually (for testing purpose)
                self.logger.info("Received manual S3 incoming file message: %s", json.dumps(message))
                handle_incoming_file(message)
            elif "Records" in message:
                # Received when file is uploaded to S3 by user
                self.logger.info("Received S3 incoming file message: %s", json.dumps(message))
                for record in message['Records']:
                    if record["eventName"].startswith("ObjectCreated:"):
                        key = record['s3']['object']['key']
                        self.logger.info("Received S3 event for key: %s", key)
                        handle_incoming_file({"s3_key": key})
            elif "Message" in message:
                # Received when Textract sends a response
                self.logger.info("Received textract response: ")
                message_body = json.loads(message['Message'])
                process_textract_message(message_body)
            elif message.get('Event') == "s3:TestEvent":
                # Received when S3 sends a test event
                self.logger.info("Received S3 test event: %s", message)
                # No action needed for test events
            else:
                raise NotImplementedError("Unknown message type received: %s" % str(message))

        except Exception as e:
            self.logger.exception(e)
