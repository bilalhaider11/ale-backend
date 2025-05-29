#!/usr/bin/env python3
import os
import sys
import time
import boto3
import json
from common.app_config import config
from common.app_logger import create_logger
from processor import OrganizationProcessor
from setup import setup_organization_processor_queue

logger = create_logger()

def main():
    """Main entry point for the organization processor service"""
    logger.info("Starting organization processor service")
    
    # Purge the queue to remove old messages
    from setup import purge_organization_processor_queue
    purge_result = purge_organization_processor_queue()
    logger.info(f"Queue purge result: {purge_result}")
    
    # Set up the queue
    queue_info = setup_organization_processor_queue()
    queue_url = queue_info['QueueUrl']
    
    # Initialize the processor
    processor = OrganizationProcessor()
    
    # Initialize SQS client
    sqs = boto3.client(
        'sqs',
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
        region_name=config.AWS_REGION
    )
    
    logger.info(f"Listening for messages on queue: {queue_url}")
    
    # Main processing loop
    while True:
        try:
            # Receive messages from SQS
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
                VisibilityTimeout=60  # Increased timeout to allow more processing time
            )
            
            messages = response.get('Messages', [])
            
            if messages:
                logger.info(f"Received {len(messages)} messages")
                
                for message in messages:
                    receipt_handle = message['ReceiptHandle']
                    
                    # Parse the message body
                    try:
                        message_body = json.loads(message.get('Body', '{}'))
                    except json.JSONDecodeError:
                        message_body = message.get('Body', {})
                    
                    # Process the message
                    try:
                        success = processor.process(message_body)
                        
                        if success:
                            # Delete the message from the queue if processed successfully
                            sqs.delete_message(
                                QueueUrl=queue_url,
                                ReceiptHandle=receipt_handle
                            )
                            logger.info(f"Message processed and deleted")
                        else:
                            # If processing failed, log it but still delete to prevent infinite retries
                            logger.warning(f"Message processing returned False, but deleting to prevent infinite retries")
                            sqs.delete_message(
                                QueueUrl=queue_url,
                                ReceiptHandle=receipt_handle
                            )
                    except Exception as e:
                        logger.exception(f"Error processing message: {str(e)}")
                        # Delete the message to prevent infinite retries
                        sqs.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=receipt_handle
                        )
                        logger.info(f"Deleted message despite error to prevent infinite retries")
            else:
                logger.debug("No messages received")
                
            # Small delay to prevent tight looping
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in main processing loop: {str(e)}")
            time.sleep(5)  # Wait a bit before retrying

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error(str(e))
        print(f'"Organization-Processor" running at version: "0.0.1"')
        sys.exit(1)
