from rococo.messaging import BaseServiceProcessor

from common.app_logger import create_logger, set_rollbar_exception_catch


class FileProcessor(BaseServiceProcessor):  # pylint: disable=R0903
    """
    Service processor that processes files from SQS messages
    """
    def __init__(self):
        super().__init__()
        self.logger = create_logger()
        set_rollbar_exception_catch()

    def process(self, message):
        """Main processor loop"""
        try:
            self.logger.info("Processing message: %s", message)
            self.logger.info("Message type: %s", type(message))
        except Exception as e:
            self.logger.exception(e)
