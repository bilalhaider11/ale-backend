from common.app_logger import create_logger, set_rollbar_exception_catch
from common.app_config import config
from rococo.messaging import BaseServiceProcessor
from lib.handler import message_handler

# This is an example implementation of a BaseServiceProcessor class.
# This should be done in the child image
class OigVerifierProcessor(BaseServiceProcessor):
    """
    Service processor that handles OIG verification messages
    """

    def __init__(self):
        super().__init__()
        self.logger = create_logger()
        set_rollbar_exception_catch()
        # Initialize any other resources needed for the processor

    def process(self, message):
        self.logger.info("Received message: %s to the OIG verifier service!", message)
        # Do something with the message
        # For example, you can call a method from the service's lib directory
        try:
            message_handler(message)
        except Exception as e:
            self.logger.error(f"Error running OIG verifier service: {str(e)}")
            self.logger.exception(e) 