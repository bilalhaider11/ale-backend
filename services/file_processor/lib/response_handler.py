from common.app_logger import logger
from common.services import S3ClientService
from common.models import FileStatusEnum

from lib.textract_client import TextractClient
from lib.file_utils import get_file_by_id, update_file, get_processed_data_key


textract_client = TextractClient()
s3_client = S3ClientService()


def process_textract_message(message):
    """
    Handles the response from Textract.
    """

    logger.info("Handling Textract response...")
    logger.info(message)
    
    # Extract relevant information from the message
    job_id = message.get('JobId')
    status = message.get('Status')
    file_id = message.get('JobTag')

    file = get_file_by_id(file_id)

    if status == 'SUCCEEDED':
        logger.info("Textract job %s succeeded.", job_id)
        # Process the results
        results = textract_client.get_document_analysis(job_id)
        logger.info("Results: %s", len(results))
        data_s3_key = get_processed_data_key(file.entity_id)
        s3_client.upload_json(data_s3_key, results)
        file.status = FileStatusEnum.SUCCEEDED
        update_file(file)

    elif status == 'FAILED':
        logger.error("Textract job %s failed.", job_id)
        file.status = FileStatusEnum.FAILED
        update_file(file)
    else:
        logger.warning("Unknown status for job %s: %s", job_id, status)
