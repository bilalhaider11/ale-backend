import os
import boto3
from common.app_config import config
from common.app_logger import logger


def setup_organization_processor_queue():
    """
    Set up the SQS queue for the organization processor
    
    Returns:
        dict: Information about the created queue
    """
    # Initialize AWS clients
    sqs = boto3.client(
        'sqs',
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
        region_name=config.AWS_REGION
    )
    
    queue_name = config.PREFIXED_ORGANIZATION_PROCESSOR_QUEUE_NAME
    
    # Step 1: Create or get the SQS queue
    try:
        logger.info(f"Checking if SQS queue exists: {queue_name}")
        queue_url = sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
        logger.info(f"Queue exists: {queue_url}")
    except sqs.exceptions.QueueDoesNotExist:
        logger.info(f"Queue does not exist. Creating: {queue_name}")
        queue_url = sqs.create_queue(
            QueueName=queue_name,
            Attributes={
                'VisibilityTimeout': '30',  # 30 seconds
                'MessageRetentionPeriod': '86400',  # 1 day
                'ReceiveMessageWaitTimeSeconds': '20'  # Long polling
            }
        )['QueueUrl']
        logger.info(f"Queue created: {queue_url}")
    
    # Get Queue ARN
    attrs = sqs.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['QueueArn']
    )
    queue_arn = attrs['Attributes']['QueueArn']
    
    logger.info(f"Organization processor queue setup complete: {queue_name}")
    
    return {
        'QueueUrl': queue_url,
        'QueueArn': queue_arn,
        'QueueName': queue_name
    }

if __name__ == "__main__":
    # Test the setup function
    queue_info = setup_organization_processor_queue()
    print(f"Queue URL: {queue_info['QueueUrl']}")
    print(f"Queue ARN: {queue_info['QueueArn']}")
