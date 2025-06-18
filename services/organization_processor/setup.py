import os
import boto3
import json
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


def setup_s3_to_sqs_notification_for_logos():
    """
    Set up S3 bucket notification to send messages to SQS when logo files are uploaded
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize AWS clients
        s3 = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
            region_name=config.AWS_REGION
        )
        
        sqs = boto3.client(
            'sqs',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
            region_name=config.AWS_REGION
        )
        
        bucket_name = config.AWS_S3_LOGOS_BUCKET_NAME
        queue_name = config.PREFIXED_ORGANIZATION_PROCESSOR_QUEUE_NAME
        
        # Get queue URL and ARN
        queue_url_response = sqs.get_queue_url(QueueName=queue_name)
        queue_url = queue_url_response['QueueUrl']
        
        queue_attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )
        queue_arn = queue_attrs['Attributes']['QueueArn']
        
        # Create SQS policy to allow S3 to send messages
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "s3.amazonaws.com"
                    },
                    "Action": "sqs:SendMessage",
                    "Resource": queue_arn,
                    "Condition": {
                        "ArnEquals": {
                            "aws:SourceArn": f"arn:aws:s3:::{bucket_name}"
                        }
                    }
                }
            ]
        }
        
        # Set the queue policy
        sqs.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes={
                'Policy': json.dumps(policy)
            }
        )
        
        logger.info(f"Set SQS policy to allow S3 notifications from bucket: {bucket_name}")
        
        # Configure S3 bucket notification
        notification_config = {
            'QueueConfigurations': [
                {
                    'Id': 'OrganizationLogoUpload',
                    'QueueArn': queue_arn,
                    'Events': ['s3:ObjectCreated:*'],
                    'Filter': {
                        'Key': {
                            'FilterRules': [
                                {
                                    'Name': 'prefix',
                                    'Value': 'organizations/'
                                },
                            ]
                        }
                    }
                }
            ]
        }
        
        # Apply the notification configuration
        s3.put_bucket_notification_configuration(
            Bucket=bucket_name,
            NotificationConfiguration=notification_config
        )
        
        logger.info(f"Successfully configured S3 bucket notification for logo uploads")
        return True
        
    except Exception as e:
        logger.exception(f"Error setting up S3 to SQS notification: {e}")
        return False


if __name__ == "__main__":
    # Test the setup functions
    queue_info = setup_organization_processor_queue()
    print(f"Queue URL: {queue_info['QueueUrl']}")
    print(f"Queue ARN: {queue_info['QueueArn']}")
    
    # Setup S3 to SQS notification
    s3_notification_success = setup_s3_to_sqs_notification_for_logos()
    print(f"S3 notification setup: {'Success' if s3_notification_success else 'Failed'}")
