from common.app_logger import create_logger
from common.app_config import config
from lib.image_conversion import convert_image_to_png
from io import BytesIO
import boto3

logger = create_logger()

def process_s3_event(message):
    """
    Process S3 event messages for logo uploads
    
    Args:
        message: S3 event message
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Extract S3 event details
        for record in message.get("Records", []):
            event_name = record.get("eventName", "")
            
            # Only process object creation events
            if not event_name.startswith("ObjectCreated:"):
                continue
            
            s3_info = record.get("s3", {})
            bucket_name = s3_info.get("bucket", {}).get("name")
            object_key = s3_info.get("object", {}).get("key")
            
            if not bucket_name or not object_key:
                logger.error("Missing bucket name or object key in S3 event")
                continue
            
            logger.info(f"Processing S3 event: {event_name} for {bucket_name}/{object_key}")
            
            # Log the received S3 event details
            logger.info(f"S3 Event - Bucket: {bucket_name}, Key: {object_key}")
            
            key_parts = object_key.split("/")
            if len(key_parts) >= 4 and key_parts[0] == "organizations" and key_parts[2] == "logo-raw":
                organization_id = key_parts[1]
                
                # Get organization
                from common.services.organization import OrganizationService
                org_service = OrganizationService(config)
                organization = org_service.get_organization_by_id(organization_id)
                
                if not organization:
                    logger.error(f"Organization not found: {organization_id}")
                    continue
                
                # Process the logo
                success = process_logo_from_s3(organization, bucket_name, object_key)
                
                if not success:
                    logger.error(f"Failed to process logo from S3: {object_key}")
                    return False
                    
        return True
        
    except Exception as e:
        logger.exception(f"Error processing S3 event: {e}")
        return False

def process_logo_from_s3(organization, bucket_name, object_key):
    """
    Download logo from S3, convert to PNG, and re-upload
    
    Args:
        organization: Organization object
        bucket_name: S3 bucket name
        object_key: S3 object key
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
            region_name=config.AWS_REGION
        )
        
        # Download the raw logo
        logger.info(f"Downloading logo from S3: {bucket_name}/{object_key}")
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        raw_logo_data = response['Body'].read()
        
        # Convert to PNG
        png_bytes, conversion_success = convert_image_to_png(raw_logo_data, source_type="bytes")
        
        if not conversion_success or not png_bytes:
            logger.error("Failed to convert logo to PNG")
            return False
        
        # Upload the PNG version
        png_key = f"organizations/{organization.entity_id}/logo.png"
        
        logger.info(f"Uploading PNG logo to S3: {png_key}")
        s3.upload_fileobj(
            BytesIO(png_bytes),
            bucket_name,
            png_key,
            ExtraArgs={
                'ContentType': 'image/png',
                'Metadata': {
                    'organization_id': organization.entity_id,
                    'source_key': object_key
                },
                'CacheControl': 'no-cache, no-store, must-revalidate'
            }
        )
        
        from common.services.organization import OrganizationService
        org_service = OrganizationService(config)
        org_service.update_logo_url(organization.entity_id, png_key)
        
        logger.info(f"Successfully processed logo for organization {organization.entity_id}")
        return True
        
    except Exception as e:
        logger.exception(f"Error processing logo from S3: {e}")
        return False

