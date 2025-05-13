import boto3
import os

from common.app_config import config
from common.app_logger import logger

class TextractClient:
    def __init__(self):
        self.client = boto3.client(
            'textract',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
            region_name=config.AWS_REGION
        )

        self.bucket_name = config.AWS_S3_BUCKET_NAME

    def start_document_analysis(self, document_key, feature_types=None, client_request_token=None, job_tag=None):
        """
        Starts asynchronous analysis of a document in S3.
        """
        if feature_types is None:
            feature_types = ["TABLES", "FORMS"]

        params = {
            'DocumentLocation': {
                'S3Object': {
                    'Bucket': self.bucket_name,
                    'Name': document_key
                }
            },
            'FeatureTypes': feature_types,
            'NotificationChannel': {
                'SNSTopicArn': os.environ.get('DOCUMENT_ANALYSIS_RESPONSE_TOPIC_ARN'),
                'RoleArn': os.environ.get('TEXTRACT_PUBLISH_ROLE_ARN')
            },
            'JobTag': job_tag
        }

        if client_request_token:
            params['ClientRequestToken'] = client_request_token

        response = self.client.start_document_analysis(**params)
        logger.info(f"Started document analysis job with ID: {response['JobId']}")
        logger.info(f"Response: {response}")
        return response['JobId']

    def get_document_analysis(self, job_id):
        """
        Retrieves the results of a document analysis job.
        Automatically handles pagination to get all results.
        """
        results = []
        next_token = None

        while True:
            if next_token:
                response = self.client.get_document_analysis(JobId=job_id, NextToken=next_token)
            else:
                response = self.client.get_document_analysis(JobId=job_id)

            results.extend(response.get('Blocks', []))
            next_token = response.get('NextToken')

            if not next_token:
                break

        return results
