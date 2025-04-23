from common.app_logger import logger
from common.services import S3ClientService
from common.models import File, FileStatusEnum
from common.constants.content_types import TEXTRACT_ACCEPTED_CONTENT_TYPES, CONVERTABLE_CONTENT_TYPES
import tempfile
import zipfile
from lib.file_utils import get_local_file_content_type, save_incoming_file, update_file, save_extracted_file, get_processed_file_key
from lib.textract_client import TextractClient
from lib.file_conversion import handle_s3_file_conversion, handle_local_file_conversion

import os
import shutil


s3_client = S3ClientService()
textract_client = TextractClient()



def handle_incoming_file(message: dict):
    """Process the message to handle incoming file for preprocessing."""                                                                                                 
    s3_key = message.get('s3_key')
    if not s3_key:
        raise ValueError("No s3_key found in message.")

    # Make a temporary directory to process files
    content_type = s3_client.get_file_content_type(s3_key)
    file = save_incoming_file(s3_key)

    if content_type == "application/zip":
        logger.info("Received a zip file... Downloading and extracting...")
        try:
            zip_file_path = download_file(file)
            handle_zip_file(zip_file_path, source_file=file)
            file.status = FileStatusEnum.EXTRACTED
            update_file(file)
        except Exception as e:
            file.status = FileStatusEnum.ERROR
            update_file(file)
            raise e
    
    elif content_type in TEXTRACT_ACCEPTED_CONTENT_TYPES:
        logger.info("Received a textractable file... Uploading as-is to processed directory...")
        try:
            processed_s3_key = get_processed_file_key(file.organization_id, file.entity_id)
            s3_client.copy_object(s3_key, processed_s3_key)
            start_textract_job(file)
        except Exception as e:
            file.status = FileStatusEnum.ERROR
            update_file(file)
            raise e

    elif content_type in CONVERTABLE_CONTENT_TYPES:
        logger.info("Received a convertable file... Converting file...")
        try:
            handle_s3_file_conversion(file)
            file.status = FileStatusEnum.CONVERTED
            update_file(file)
            start_textract_job(file)
        except Exception as e:
            file.status = FileStatusEnum.ERROR
            update_file(file)
            raise e

    else:
        raise NotImplementedError("Unsupported file type: %s" % content_type)


def handle_zip_file(zip_file_path: str, source_file: File):
    """Extracts a ZIP file, processes supported files recursively, and starts Textract jobs where applicable."""

    def should_ignore(filename: str) -> bool:
        """Returns True if the file is hidden or a known system-generated file."""

        IGNORED_PATHS = [
            '__MACOSX/',
            '.DS_Store',
            'Thumbs.db',
            'desktop.ini',
        ]
        basename = os.path.basename(filename)
        return (
            any(part.startswith('.') for part in filename.split(os.sep)) or
            any(basename.lower() == name.lower() for name in IGNORED_PATHS)
        )

    # Implement the logic to extract the zip file
    extracted_dir = extract_zip_file(zip_file_path)

    # walk through the extracted directory and process each file
    for root, _, files in os.walk(extracted_dir):
        for file in files:
            file_path = os.path.join(root, file)

            if should_ignore(file_path):
                continue

            # Check file content type
            content_type = get_local_file_content_type(file_path)
            if content_type == "application/zip":
                handle_zip_file(file_path, source_file=source_file)

            elif content_type in TEXTRACT_ACCEPTED_CONTENT_TYPES:
                # Upload the file to processed directory
                logger.info("Processing file: %s", file_path)
                try:
                    file = save_extracted_file(file_path, source_file=source_file)
                    s3_key = get_processed_file_key(file.organization_id, file.entity_id)
                    s3_client.upload_file(file_path, s3_key, content_type=file.content_type)
                    start_textract_job(file)
                except Exception as e:
                    file.status = FileStatusEnum.ERROR
                    update_file(file)
                    logger.error("Failed to process local file in ZIP. Filename: %s, Content type: %s", file.filename, file.content_type)
                    logger.error(e)

            elif content_type in CONVERTABLE_CONTENT_TYPES:
                # Convert and upload the file to processed directory
                logger.info("Converting file: %s", file_path)
                try:
                    file = save_extracted_file(file_path, source_file=source_file)
                    handle_local_file_conversion(file, file_path)
                    file.status = FileStatusEnum.CONVERTED
                    update_file(file)
                    start_textract_job(file)
                except Exception as e:
                    logger.error("Failed to convert and process local file in ZIP. Filename: %s, Content type: %s", file.filename, file.content_type)
                    logger.error(e)
                    file.status = FileStatusEnum.ERROR
                    update_file(file)
            else:
                logger.info("Unsupported file type encountered... %s" % content_type)

    shutil.rmtree(extracted_dir)  # Clean up the extracted directory


def extract_zip_file(zip_file_path: str):
    """Extracts the zip file to a temporary directory."""
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    return temp_dir


def download_file(file: File, download_dir: str = None):
    """Download a file from S3 to a temporary directory."""
    if not download_dir:
        download_dir = tempfile.mkdtemp()
    file_path = os.path.join(download_dir, file.s3_key)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    s3_client.download_file(file.s3_key, file_path)
    return file_path


def start_textract_job(file: File):
    """Starts a Textract analysis job for the given file and updates its status to IN_PROGRESS."""

    processed_s3_key = get_processed_file_key(file.organization_id, file.entity_id)
    job_id = textract_client.start_document_analysis(processed_s3_key, job_tag=file.entity_id)
    file.status = FileStatusEnum.IN_PROGRESS
    update_file(file)
    return job_id
