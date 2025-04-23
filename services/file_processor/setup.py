import os
import boto3
import json
from common.app_config import config
from common.app_logger import logger

AWS_CONFIG = dict(
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
    region_name=config.AWS_REGION
)

def setup_textract_notification_channel(topic_name, queue_name):


    sns = boto3.client('sns', **AWS_CONFIG)
    sqs = boto3.client('sqs', **AWS_CONFIG)
    iam = boto3.client('iam', **AWS_CONFIG)
    sts = boto3.client('sts', **AWS_CONFIG)

    # Step 1: Create or get SNS topic
    logger.info("Ensuring SNS topic exists: %s", topic_name)
    topic_response = sns.create_topic(Name=topic_name)
    topic_arn = topic_response['TopicArn']
    logger.info("Topic ARN: %s", topic_arn)

    # Step 2: Get or create SQS queue
    try:
        logger.info("Checking if SQS queue exists: %s", queue_name)
        queue_url = sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
    except sqs.exceptions.QueueDoesNotExist:
        logger.info("Queue does not exist. Creating: %s", queue_name)
        queue_url = sqs.create_queue(QueueName=queue_name)['QueueUrl']

    # Get the Queue ARN
    attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['QueueArn', 'Policy'])
    queue_arn = attrs['Attributes']['QueueArn']
    existing_policy = attrs.get('Attributes', {}).get('Policy')
    logger.info("Queue ARN: %s", queue_arn)

    # Step 3: Upsert queue policy to allow SNS to send messages.
    policy_id = "Allow-SendMessage"
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

    sns_publish_statement = {
        "Sid": "AllowSNSPublish",
        "Effect": "Allow",
        "Principal": {"Service": "sns.amazonaws.com"},
        "Action": "SQS:SendMessage",
        "Resource": queue_arn,
        "Condition": {
            "ArnEquals": {"aws:SourceArn": topic_arn}
        }
    }

    statements = [
        statement for statement in statements
        if statement.get('Sid') != sns_publish_statement['Sid']
    ]

    statements.append(sns_publish_statement)
    policy_json["Statement"] = statements

    sqs.set_queue_attributes(
        QueueUrl=queue_url,
        Attributes={
            'Policy': json.dumps(policy_json)
        }
    )
    logger.info("Queue policy set to allow SNS to send messages")

    # Step 4: Check for existing subscription
    existing_subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn)['Subscriptions']
    already_subscribed = any(
        sub['Endpoint'] == queue_arn and sub['Protocol'] == 'sqs'
        for sub in existing_subs
    )

    if already_subscribed:
        logger.info("Queue is already subscribed to the topic. Skipping subscription.")
        subscription_arn = next(
            sub['SubscriptionArn'] for sub in existing_subs
            if sub['Endpoint'] == queue_arn and sub['Protocol'] == 'sqs'
        )
    else:
        logger.info("Subscribing queue to SNS topic")
        subscribe_response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='sqs',
            Endpoint=queue_arn,
            ReturnSubscriptionArn=True
        )
        subscription_arn = subscribe_response['SubscriptionArn']
        logger.info("Subscription ARN: %s", subscription_arn)

    # Step 5: Set up Textract Role for publishing to SNS
    ROLE_NAME = "TextractDocumentAnalysisSNSPublishRole"
    try:
        role_response = iam.get_role(RoleName=ROLE_NAME)
        role_arn = role_response['Role']['Arn']
    except iam.exceptions.NoSuchEntityException:
        # Role doesn't exist, create it
        account_id = sts.get_caller_identity()["Account"]
        role_arn = f"arn:aws:iam::{account_id}:role/{ROLE_NAME}"

        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "textract.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }

        iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Allows Textract to publish to SNS"
        )

        # Attach SNS publish permissions
        policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": "sns:Publish",
                "Resource": topic_arn
            }]
        }

        iam.put_role_policy(
            RoleName=ROLE_NAME,
            PolicyName="TextractSNSPublishPolicy",
            PolicyDocument=json.dumps(policy)
        )

    os.environ['DOCUMENT_ANALYSIS_RESPONSE_TOPIC_ARN'] = topic_arn
    os.environ['TEXTRACT_PUBLISH_ROLE_ARN'] = role_arn
    os.environ['FILE_PROCESSOR_QUEUE_URL'] = queue_url
    os.environ['FILE_PROCESSOR_QUEUE_ARN'] = queue_arn
    os.environ['FILE_PROCESSOR_SUBSCRIPTION_ARN'] = subscription_arn



def setup_s3_to_sqs_notification(bucket_name, queue_name, s3_prefix_filter, region='us-east-1'):
    sqs = boto3.client('sqs', **AWS_CONFIG)
    s3 = boto3.client('s3', **AWS_CONFIG)

    # Step 1: Create or get the SQS queue
    try:
        logger.info("Checking if SQS queue exists: %s", queue_name)
        queue_url = sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
    except sqs.exceptions.QueueDoesNotExist:
        logger.info("Queue does not exist. Creating: %s", queue_name)
        queue_url = sqs.create_queue(QueueName=queue_name)['QueueUrl']

    # Get Queue ARN
    attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['QueueArn', 'Policy'])
    queue_arn = attrs['Attributes']['QueueArn']
    existing_policy = attrs.get('Attributes', {}).get('Policy')
    logger.info("Queue ARN: %s", queue_arn)

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
    logger.info("Bucket notification configuration updated")

    return {
        'Bucket': bucket_name,
        'QueueUrl': queue_url,
        'QueueArn': queue_arn,
        'Prefix': s3_prefix_filter
    }

# Example usage
if __name__ == '__main__':
    setup_textract_notification_channel(
        config.PREFIXED_DOCUMENT_ANALYSIS_RESPONSE_TOPIC_NAME, 
        config.PREFIXED_FILE_PROCESSOR_QUEUE_NAME
    )
    setup_s3_to_sqs_notification(
        bucket_name=config.AWS_S3_BUCKET_NAME,
        queue_name=config.PREFIXED_FILE_PROCESSOR_QUEUE_NAME,
        s3_prefix_filter=os.path.join(config.AWS_S3_KEY_PREFIX, 'incoming/')
    )
