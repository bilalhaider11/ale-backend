from common.app_logger import create_logger
from common.app_config import config
import base64
from io import BytesIO
import boto3
import os

logger = create_logger()

def process_logo(organization, logo_data):
    """
    Process organization logo
    
    Args:
        organization: Organization object
        logo_data: URL of the logo or dict with base64 content
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Processing logo for organization {organization.entity_id}")
    
    if not logo_data:
        logger.error("No valid logo data provided")
        return False
    
    try:
        # Check if logo_data is a URL string
        if isinstance(logo_data, str):
            # Handle as URL
            logo_url = logo_data
            
            # If the logo is already in CloudFront, just update the organization
            cloudfront_domain = f"https://{config.CLOUDFRONT_DISTRIBUTION_DOMAIN}"
            if logo_url.startswith(cloudfront_domain):
                logger.info(f"Logo already in CloudFront: {logo_url}")
                
                # Update the organization with the logo URL directly
                from common.services.organization import OrganizationService
                organization_service = OrganizationService(config)
                
                # Check if the logo_url is already set on the organization
                if getattr(organization, 'logo_url', None) != logo_url:
                    update_result = organization_service.update_organization(
                        organization.entity_id, 
                        {"logo_url": logo_url}
                    )
                    
                    logger.info(f"Organization logo URL updated")
                    
                return True
                
            # Transfer logo from URL to S3
            file_ext = "jpeg"  # Default extension
            new_logo_url = transfer_logo_to_s3(
                organization.entity_id,
                logo_url,
                file_ext=file_ext,
                source_type="url"
            )
            
            if not new_logo_url:
                logger.error(f"Failed to upload logo to S3")
                return False
            
        # Handle base64 encoded file data
        elif isinstance(logo_data, dict) and 'content' in logo_data:
            logger.info(f"Processing base64 encoded logo for organization {organization.entity_id}")
            logger.info(f"Logo data keys: {logo_data.keys()}")
            
            # Extract file data
            content = logo_data.get('content')
            content_type = logo_data.get('content_type', 'image/jpeg')
            filename = logo_data.get('filename', 'logo.jpg')
            
            # Get file extension from filename
            file_ext = filename.split('.')[-1] if '.' in filename else 'jpg'
            
            # Transfer base64 content to S3
            new_logo_url = transfer_logo_to_s3(
                organization.entity_id,
                content,
                file_ext=file_ext,
                content_type=content_type,
                source_type="base64"
            )
            
            if not new_logo_url:
                logger.error(f"Failed to upload base64 logo to S3")
                return False
            
        else:
            logger.error(f"Unsupported logo data format: {type(logo_data)}")
            return False
        
        # Update the organization with the new logo URL
        from common.services.organization import OrganizationService
        organization_service = OrganizationService(config)
        update_result = organization_service.update_organization(
            organization.entity_id, 
            {"logo_url": new_logo_url}
        )
        
        logger.info(f"Organization logo URL updated to: {new_logo_url}")
        return True
            
    except Exception as e:
        logger.exception(f"Error processing logo: {e}")
        return False

def transfer_logo_to_s3(organization_id, source_data, file_ext="jpeg", content_type="image/jpeg", source_type="url"):
    """
    Transfer logo to S3 from either URL or base64 content
    
    Args:
        organization_id: ID of the organization
        source_data: Either URL string or base64 content
        file_ext: File extension for the logo
        content_type: MIME type of the image
        source_type: Either "url" or "base64"
        
    Returns:
        str: CloudFront URL of the uploaded logo, or None if failed
    """
    try:
        # Generate a key for the logo with file extension
        destination_key = f"organizations/{organization_id}/logo.{file_ext}"
        
        # Prepare the full key with prefix
        key_prefix = getattr(config, 'AWS_S3_KEY_PREFIX', '')
        key_prefix = os.path.join(key_prefix, 'organization-logo/') if key_prefix else 'organization-logo/'
        
        # Replace backslashes with forward slashes for S3 paths
        key_prefix = key_prefix.replace('\\', '/')
        
        # Ensure the key prefix ends with a slash
        if not key_prefix.endswith('/'):
            key_prefix += '/'
            
        full_key = f"{key_prefix}{destination_key}"
        
        # Initialize S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
            region_name=config.AWS_REGION
        )
        
        bucket_name = config.AWS_S3_LOGOS_BUCKET_NAME
        
        # Handle URL source
        if source_type == "url":
            # Use the organization-specific S3 client
            from lib.s3_client import OrganizationS3Client
            s3_client = OrganizationS3Client()
            
            # Update the key prefix in the client
            s3_client.key_prefix = key_prefix
            
            # Upload the logo from URL to S3
            upload_result = s3_client.upload_from_url(
                url=source_data,
                s3_key=destination_key,
                content_type=content_type,
                metadata={"organization_id": str(organization_id)}
            )
            
            if not upload_result:
                logger.error(f"Failed to upload logo from URL to S3")
                return None
                
        # Handle base64 source
        elif source_type == "base64":
            try:
                # Decode base64 content
                file_content = base64.b64decode(source_data)
                
                logger.info(f"Decoded base64 content, size: {len(file_content)} bytes")
                
                logger.info(f"Uploading to S3 bucket: {bucket_name}, key: {full_key}")
                
                # Upload the file
                s3.upload_fileobj(
                    BytesIO(file_content),
                    bucket_name,
                    full_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'Metadata': {"organization_id": str(organization_id)},
                    }
                )
                
                logger.info(f"Successfully uploaded logo to S3")
                
            except Exception as e:
                logger.exception(f"Error uploading logo to S3: {e}")
                return None
        else:
            logger.error(f"Unsupported source type: {source_type}")
            return None
            
        # Generate CloudFront URL
        cloudfront_domain = f"https://{config.CLOUDFRONT_DISTRIBUTION_DOMAIN}"
        cloudfront_url = f"{cloudfront_domain}/{full_key}"
        
        logger.info(f"Generated CloudFront URL: {cloudfront_url}")
        return cloudfront_url
        
    except Exception as e:
        logger.exception(f"Error transferring logo to S3: {e}")
        return None
