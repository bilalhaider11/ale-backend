from PIL import Image
import os
import tempfile

from common.models import File
from common.services import S3ClientService
from common.services.filestack_client import FileStackClient
from common.constants.content_types import IMAGE_CONTENT_TYPES, DOCUMENT_CONTENT_TYPES
from lib.file_utils import get_processed_file_key

s3_client = S3ClientService()
filestack_client = FileStackClient()




def convert_image(input_path):
    """
    Converts any image format to PNG.

    Args:
        input_path (str): Path to the input image file.
        output_path (str, optional): Path to save the PNG. If None, replaces extension with .png.

    Returns:
        str: Path to the saved PNG file.
    """
    try:
        # Open image
        with Image.open(input_path) as img:
            # Convert to RGBA if necessary (handles alpha/transparency)
            if img.mode in ("P", "LA", "RGBA", "RGBa", "CMYK"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")

            # Determine output path
            base, _ = os.path.splitext(input_path)
            output_path = f"{base}.png"

            # Save as PNG
            img.save(output_path, format="PNG")

            return output_path

    except Exception as e:
        raise RuntimeError(f"Failed to convert {input_path} to PNG: {e}")
    


def handle_s3_file_conversion(file: File):
    if file.content_type in IMAGE_CONTENT_TYPES:
        # Convert from Pillow
        temp_dir = tempfile.mkdtemp()
        filename = file.filename
        file_path = os.path.join(temp_dir, filename)
        s3_client.download_file(file.s3_key, file_path)
        converted_file_path = convert_image(file_path)
        processed_s3_key = get_processed_file_key(file.organization_id, file.entity_id)
        s3_client.upload_file(converted_file_path, processed_s3_key)

    elif file.content_type in DOCUMENT_CONTENT_TYPES:
        # Convert from Filestack
        file_url = s3_client.generate_presigned_url(file.s3_key)
        pdf_url = filestack_client.convert_to_pdf_from_url(file_url)
        s3_key = get_processed_file_key(file.organization_id, file.entity_id)
        s3_client.upload_from_url(pdf_url, s3_key)

    else:
        raise NotImplementedError("Unsupported content type to be converted from S3")


def handle_local_file_conversion(file: File, local_file_path: str):
    if file.content_type in IMAGE_CONTENT_TYPES:
        # Convert from Pillow
        converted_file_path = convert_image(local_file_path)
        processed_s3_key = get_processed_file_key(file.organization_id, file.entity_id)
        s3_client.upload_file(converted_file_path, processed_s3_key)

    elif file.content_type in DOCUMENT_CONTENT_TYPES:
        # Convert from Filestack
        filelink = filestack_client.upload_file(local_file_path)
        pdf_url = filestack_client.convert_to_pdf(filelink)
        s3_key = get_processed_file_key(file.organization_id, file.entity_id)
        s3_client.upload_from_url(pdf_url, s3_key)
        filestack_client.delete_file(filelink)

    else:
        raise NotImplementedError("Unsupported content type to be converted from local file")
