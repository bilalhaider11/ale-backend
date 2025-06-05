from common.app_logger import create_logger
from common.app_config import config
from lib.image_conversion import convert_image_to_png
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
                
            # Convert and transfer logo from URL to S3
            new_logo_url = transfer_logo_to_s3(
                organization.entity_id,
                logo_url,
                source_type="url"
            )
            
            if not new_logo_url:
                logger.error(f"Failed to upload logo to S3")
                return False
            
        # Handle base64 encoded file data
        elif isinstance(logo_data, dict) and 'content' in logo_data:
            logger.info(f"Processing base64 encoded logo for organization {organization.entity_id}")
            
            # Extract file data
            content = logo_data.get('content')
            
            # Transfer base64 content to S3 (will be converted to PNG)
            new_logo_url = transfer_logo_to_s3(
                organization.entity_id,
                content,
                content_type="image/png",
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

def transfer_logo_to_s3(organization_id, source_data, content_type="image/png", source_type="url"):
    """
    Transfer logo to S3 from either URL or base64 content, converting to PNG
    
    Args:
        organization_id: ID of the organization
        source_data: Either URL string or base64 content
        content_type: MIME type of the image (should be "image/png")
        source_type: Either "url" or "base64"
        
    Returns:
        str: CloudFront URL of the uploaded logo, or None if failed
    """
    try:
        # Convert image to PNG
        png_bytes, conversion_success = convert_image_to_png(source_data, source_type)
        
        if not conversion_success or not png_bytes:
            logger.error(f"Failed to convert image to PNG")
            return None
        
        # Generate a key for the logo with PNG extension
        destination_key = f"organizations/{organization_id}/logo.png"
        full_key = destination_key

        # Initialize S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
            region_name=config.AWS_REGION
        )
        
        bucket_name = config.AWS_S3_LOGOS_BUCKET_NAME
        
        logger.info(f"Uploading PNG to S3 bucket: {bucket_name}, key: {full_key}")
        
        # Upload the PNG file
        s3.upload_fileobj(
            BytesIO(png_bytes),
            bucket_name,
            full_key,
            ExtraArgs={
                'ContentType': content_type,
                'Metadata': {"organization_id": str(organization_id)},
                'CacheControl': 'no-cache, no-store, must-revalidate'
            }
        )
        
        logger.info(f"Successfully uploaded PNG logo to S3")
            
        # Generate CloudFront URL
        cloudfront_domain = f"https://{config.CLOUDFRONT_DISTRIBUTION_DOMAIN}"
        cloudfront_url = f"{cloudfront_domain}/{full_key}"
        
        logger.info(f"Generated CloudFront URL: {cloudfront_url}")
        return cloudfront_url
        
    except Exception as e:
        logger.exception(f"Error transferring logo to S3: {e}")
        return None
