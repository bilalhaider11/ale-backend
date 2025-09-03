from common.app_logger import create_logger, set_rollbar_exception_catch
from common.app_config import config
from rococo.messaging import BaseServiceProcessor
from lib.handler import AlertMessageHandler


class AlertProcessor(BaseServiceProcessor):
    """
    Service processor that handles alert messages
    """

    def __init__(self):
        super().__init__()
        self.logger = create_logger()
        set_rollbar_exception_catch()
        self.alert_handler = AlertMessageHandler()

    def process(self, message):
        self.logger.info("Received message: %s to the alert service!", message)
        try:
            self.alert_handler.process_message(message)
        except Exception as e:
            self.logger.error(f"Error processing alert message: {str(e)}")
            self.logger.exception(e)
