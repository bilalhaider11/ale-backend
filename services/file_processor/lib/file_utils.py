import datetime
import mimetypes
import os

from common.app_config import config
from common.models import File, FileStatusEnum
from common.services import S3ClientService
from common.services import FileService
from common.app_logger import logger


s3_client = S3ClientService()


def get_local_file_content_type(file_path):
    content_type, _ = mimetypes.guess_type(file_path)
    return content_type or 'application/octet-stream'  # fallback if unknown


def save_incoming_file(s3_key):
    "Saves incoming file uploaded to S3 to database."

    file_key = s3_key
    if s3_key.startswith(config.AWS_S3_KEY_PREFIX):
        file_key = s3_key[len(config.AWS_S3_KEY_PREFIX):]

    filename = None
    if file_key.startswith("incoming/system"):
        org_id, filename = s3_key.split("/")[-2:]
        person_id = None
    elif file_key.startswith("incoming/user"):
        org_id, person_id, filename = s3_key.split("/")[-3:]
    else:
        raise NotImplementedError()

    file_metadata = s3_client.get_object_metadata(s3_key)
    filename = file_metadata.get('filename') or filename
    content_type = file_metadata.get('ContentType')
    size_bytes = file_metadata.get('ContentLength')
    uploaded_at = file_metadata.get('LastModified')

    file_service = FileService(config)
    
    file = File(
        organization_id=org_id,
        person_id=person_id,
        filename=filename,
        s3_key=s3_key,
        content_type=content_type,
        size_bytes=size_bytes,
        uploaded_at=uploaded_at,
        status=FileStatusEnum.UPLOADED
    )

    file = file_service.save_file(file)
    return file


def save_extracted_file(file_path: str, source_file: File):
    """
    Saves a file extracted from a ZIP archive to the database.

    Args:
        file_path (str): Local file path of the extracted file.
        source_file (File): The source ZIP file (already in DB) this was extracted from.
    """
    # Extract metadata from the local file
    content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    size_bytes = os.path.getsize(file_path)
    uploaded_at = source_file.uploaded_at

    # Save metadata in DB
    file_service = FileService(config)

    extracted_file = File(
        organization_id=source_file.organization_id,
        person_id=source_file.person_id,
        filename=os.path.basename(file_path),
        s3_key=None,
        content_type=content_type,
        size_bytes=size_bytes,
        uploaded_at=uploaded_at,
        source_file_id=source_file.entity_id,
        status=FileStatusEnum.UPLOADED
    )

    extracted_file = file_service.save_file(extracted_file)
    return extracted_file


def update_file(file: File):
    file_service = FileService(config)
    file = file_service.save_file(file)
    return file

def get_file_by_id(file_id: str):
    file_service = FileService(config)
    file = file_service.get_file_by_id(file_id)
    return file


def get_processed_file_key(organization_id, file_id):
    prefix = config.AWS_S3_KEY_PREFIX or ""
    s3_key = os.path.join(prefix, f"processed/{organization_id}/{file_id}")
    return s3_key

def get_processed_data_key(file_id):
    prefix = config.AWS_S3_KEY_PREFIX or ""
    s3_key = os.path.join(prefix, f"processed/data/{file_id}")
    return s3_key
