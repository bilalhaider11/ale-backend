import pika
import json
import time
from pika.exchange_type import ExchangeType

from common.app_config import config
from common.app_logger import logger


def get_connection_parameters() -> pika.ConnectionParameters:
    return pika.ConnectionParameters(
        host=config.RABBITMQ_HOST,
        port=config.RABBITMQ_PORT,
        virtual_host=config.RABBITMQ_VIRTUAL_HOST,
        credentials=pika.credentials.PlainCredentials(
            username=config.RABBITMQ_USER,
            password=config.RABBITMQ_PASSWORD
        )
    )

def establish_connection(parameters: pika.ConnectionParameters, max_retries: int = 10) -> pika.BlockingConnection:
    retries = 0
    while retries < max_retries:
        try:
            connection = pika.BlockingConnection(parameters)
            return connection
        except Exception as e:
            logger.debug(f"Could not connect to messaging system. Retries {retries}")
            retries += 1
            if retries < max_retries:
                time.sleep(2 ** retries)
            else:
                logger.error("Error connecting to RabbitMQ after multiple retries")
                raise e

class MessageSender:
    def __init__(self):
        self.parameters = get_connection_parameters()

    def send_message(self, queue_name: str, data: dict, properties: pika.BasicProperties = None, exchange_name: str = None) -> None:
        """
        Sends a message to the specified RabbitMQ queue.

        :param queue_name: Name of the RabbitMQ queue to send the message to.
        :param data: The data to send to the queue as a dictionary.
        :return: None
        """
        connection = establish_connection(self.parameters)

        with connection:
            channel = connection.channel()

            if properties is None:
                properties = pika.BasicProperties(
                    delivery_mode=2,  # Make the message persistent
                )

            if exchange_name is None:
                exchange_name = ""
            else:
                channel.exchange_declare(exchange=exchange_name, exchange_type=ExchangeType.topic.value, durable=True)

            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_publish(
                exchange=exchange_name,
                routing_key=queue_name,
                body=json.dumps(data).encode(),
                properties=properties,
            )
            logger.info(f"Sent message to queue: {queue_name}")
