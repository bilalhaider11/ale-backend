import boto3
from common.app_config import config
from common.app_logger import logger

def process_subdomain(organization, subdomain):
    """
    Process organization subdomain
    
    Args:
        organization: Organization object
        subdomain: Subdomain string
        
    Returns:
        bool: True if both Route53 and database updates are successful, False otherwise
    """
    # Ensure subdomain is a string and not empty
    subdomain = str(subdomain) if subdomain else None
    if not subdomain:
        logger.error("Empty subdomain provided")
        return False
    
    logger.info(f"Processing subdomain for organization {organization.entity_id}")
    
    try:
        # Attempt to create or update the CNAME record in Route53
        route53_result = create_or_update_cname_record(organization, subdomain)
        
        # Only proceed with database update if Route53 succeeds
        if route53_result:
            from common.services.organization import OrganizationService
            organization_service = OrganizationService(config)
            
            # Get the base domain from config
            base_domain = getattr(config, 'BASE_DOMAIN', None)
            if not base_domain:
                logger.error("BASE_DOMAIN is not configured")
                return False
            
            # Construct the full domain
            full_domain = f"{subdomain}.{base_domain}"
            
            # Update the organization with the full domain
            update_result = organization_service.update_organization(
                organization.entity_id,
                {"full_domain": full_domain}
            )
            
            # Return True only if the database update succeeds
            return update_result is not None
        
        # Return False if Route53 update fails
        return False
    
    except Exception as e:
        logger.exception(f"Error processing subdomain: {e}")
        return False

def create_or_update_cname_record(organization, subdomain):
    """
    Create or update a CNAME record for an organization's subdomain
    
    Args:
        organization: The organization object
        subdomain: Subdomain string
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get configuration values
    hosted_zone_id = getattr(config, 'ROUTE53_HOSTED_ZONE_ID', None)
    base_domain = getattr(config, 'BASE_DOMAIN', None)
    
    if not hosted_zone_id or not base_domain:
        logger.warning("Route53 configuration missing (ROUTE53_HOSTED_ZONE_ID or BASE_DOMAIN)")
        return False
    
    # Construct the full domain and target domain
    full_domain = f"{subdomain}.{base_domain}"
    target_domain = getattr(config, 'CLOUDFRONT_DISTRIBUTION_DOMAIN', base_domain)
    
    logger.info(f"Creating/updating CNAME record for {full_domain} pointing to {target_domain}")
    
    try:
        # Initialize Route53 client
        route53 = boto3.client(
            'route53',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_ACCESS_KEY_SECRET,
            region_name=config.AWS_REGION
        )
        
        # Create or update the CNAME record
        response = route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': full_domain,
                            'Type': 'CNAME',
                            'TTL': 300,
                            'ResourceRecords': [
                                {'Value': target_domain}
                            ]
                        }
                    }
                ]
            }
        )
        
        logger.info("CNAME record created/updated successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error creating/updating CNAME record: {str(e)}")
        return False