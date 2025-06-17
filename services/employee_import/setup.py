import os
import boto3
import json
from common.app_config import config
from common.app_logger import logger

def setup_employee_import_queue():
    """
    Set up the SQS queue and S3 notification for employee and caregiver imports
    
    Returns:
        dict: Information about the created resources
    """
    # Initialize AWS clients
    sqs = boto3.client(
        'sqs',
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
        region_name=config.AWS_REGION
    )
    
    queue_name = config.PREFIXED_EMPLOYEE_IMPORT_PROCESSOR_QUEUE_NAME
    bucket_name = config.AWS_S3_BUCKET_NAME
    employee_prefix = "employees-list/"
    caregiver_prefix = "caregivers-list/"
    
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
    
    # Step 2: Set up S3 notifications for both prefixes
    employee_setup_result = setup_s3_to_sqs_notification(
        bucket_name=bucket_name,
        queue_name=queue_name,
        s3_prefix_filter=employee_prefix
    )
    
    caregiver_setup_result = setup_s3_to_sqs_notification(
        bucket_name=bucket_name,
        queue_name=queue_name,
        s3_prefix_filter=caregiver_prefix
    )
    
    logger.info(f"Employee and caregiver import queue setup complete")
    
    return {
        'QueueUrl': queue_url,
        'QueueArn': queue_arn,
        'QueueName': queue_name,
        'EmployeeS3Setup': employee_setup_result,
        'CaregiverS3Setup': caregiver_setup_result
    }

def setup_s3_to_sqs_notification(bucket_name, queue_name, s3_prefix_filter):
    """
    Set up S3 notification to SQS
    
    Args:
        bucket_name (str): S3 bucket name
        queue_name (str): SQS queue name
        s3_prefix_filter (str): S3 prefix filter
        region (str): AWS region
        
    Returns:
        dict: Information about the setup
    """
    sqs = boto3.client(
        'sqs',
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
        region_name=config.AWS_REGION
    )
    s3 = boto3.client(
        's3',
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
        region_name=config.AWS_REGION
    )

    # Step 1: Create or get the SQS queue
    try:
        logger.info(f"Checking if SQS queue exists: {queue_name}")
        queue_url = sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
    except sqs.exceptions.QueueDoesNotExist:
        logger.info(f"Queue does not exist. Creating: {queue_name}")
        queue_url = sqs.create_queue(QueueName=queue_name)['QueueUrl']

    # Get Queue ARN
    attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['QueueArn', 'Policy'])
    queue_arn = attrs['Attributes']['QueueArn']
    existing_policy = attrs.get('Attributes', {}).get('Policy')
    logger.info(f"Queue ARN: {queue_arn}")

    # Step 2: Upsert queue policy to allow S3 to send messages.
    policy_id = "Allow-SendMessage"
    bucket_arn = f"arn:aws:s3:::{bucket_name}"

    if existing_policy:
        policy_json = json.loads(existing_policy)
        statements = policy_json.get('Statement', [])
    else:
        policy_json = {
            "Version": "2012-10-17",
            "Id": policy_id,
            "Statement": []
        }
        statements = []

    s3_publish_statement = {
        "Sid": "AllowS3Publish",
        "Effect": "Allow",
        "Principal": "*",
        "Action": "SQS:SendMessage",
        "Resource": queue_arn,
        "Condition": {
            "ArnEquals": {"aws:SourceArn": bucket_arn}
        }
    }

    statements = [
        statement for statement in statements
        if statement.get('Sid') != s3_publish_statement['Sid']
    ]

    statements.append(s3_publish_statement)
    policy_json["Statement"] = statements

    sqs.set_queue_attributes(
        QueueUrl=queue_url,
        Attributes={
            'Policy': json.dumps(policy_json)
        }
    )
    
    logger.info("Queue policy updated to allow S3 messages")

    # Step 3: Get current notification config and ensure no duplication
    existing_config = s3.get_bucket_notification_configuration(Bucket=bucket_name)
    existing_queue_configs = existing_config.get('QueueConfigurations', [])

    # Remove duplicates
    existing_queue_configs = [
        conf for conf in existing_queue_configs
        if not (
            conf['QueueArn'] == queue_arn and
            conf.get('Filter', {}).get('Key', {}).get('FilterRules', [{}])[0].get('Value') == s3_prefix_filter
        )
    ]

    # Add new configuration
    new_config = {
        'QueueArn': queue_arn,
        'Events': ['s3:ObjectCreated:*'],
        'Filter': {
            'Key': {
                'FilterRules': [
                    {'Name': 'prefix', 'Value': s3_prefix_filter}
                ]
            }
        }
    }
    updated_queue_configs = existing_queue_configs + [new_config]

    # Step 4: Put new configuration back
    s3.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration={
            'QueueConfigurations': updated_queue_configs
        }
    )
    logger.info(f"Bucket notification configuration updated for {bucket_name} with prefix {s3_prefix_filter}")

    return {
        'Bucket': bucket_name,
        'QueueUrl': queue_url,
        'QueueArn': queue_arn,
        'Prefix': s3_prefix_filter
    }

if __name__ == "__main__":
    # Test the setup function
    setup_result = setup_employee_import_queue()
    print(f"Setup complete: {setup_result}")
