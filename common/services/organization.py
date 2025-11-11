from common.repositories.factory import RepositoryFactory, RepoType
from common.models import Organization
from common.app_logger import logger
from common.services.s3_client import S3ClientService
import uuid
from werkzeug.datastructures import FileStorage
from io import BytesIO

class OrganizationService:

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.organization_repo = self.repository_factory.get_repository(RepoType.ORGANIZATION)
        self.s3_client = S3ClientService()

    def save_organization(self, organization: Organization):
        organization = self.organization_repo.save(organization)
        return organization
    
    
    def get_employee_id_counter_from_organization(self, entity_id):
        
        return self.organization_repo.get_employee_id_counter(entity_id)

    def get_organization_by_id(self, entity_id: str):
        organization = self.organization_repo.get_one({"entity_id": entity_id})
        return organization

    def get_organization_by_subdomain(self, subdomain: str):
        organization = self.organization_repo.get_one({"subdomain": subdomain})
        return organization

    def get_organizations_with_roles_by_person(self, person_id: str):
        results = self.organization_repo.get_organizations_by_person_id(person_id)
        # Dictionary to group organizations by entity_id
        orgs_map = {}
        
        for result in results:
            if isinstance(result, dict):
                role = result.pop('role', None)
                org_id = result.get('entity_id')
                org = Organization(**result)
                org_dict = org.as_dict()

                # Add CloudFront domain to logo_url if it exists
                if org.logo_url:
                    cloudfront_domain = self.config.CLOUDFRONT_DISTRIBUTION_DOMAIN
                    if not cloudfront_domain.startswith(('http://', 'https://')):
                        cloudfront_domain = f"https://{cloudfront_domain}"
                    org_dict['logo_url'] = f"{cloudfront_domain}/{org.logo_url}"

                if org_id not in orgs_map:
                    orgs_map[org_id] = org_dict
                    orgs_map[org_id]['roles'] = []
                
                if role and role not in orgs_map[org_id]['roles']:
                    orgs_map[org_id]['roles'].append(role)

            else:
                org_id = result.entity_id
                org_dict = result.as_dict()

                # Add CloudFront domain to logo_url if it exists
                if result.logo_url:
                    cloudfront_domain = self.config.CLOUDFRONT_DISTRIBUTION_DOMAIN
                    if not cloudfront_domain.startswith(('http://', 'https://')):
                        cloudfront_domain = f"https://{cloudfront_domain}"
                    org_dict['logo_url'] = f"{cloudfront_domain}/{result.logo_url}"

                if org_id not in orgs_map:
                    orgs_map[org_id] = org_dict
                    orgs_map[org_id]['roles'] = []
                
                if hasattr(result, 'role') and result.role not in orgs_map[org_id]['roles']:
                    orgs_map[org_id]['roles'].append(result.role)

        return list(orgs_map.values())

    def get_persons_with_roles_in_organization(self, organization_id: str):
        organization_repo = self.repository_factory.get_repository(RepoType.PERSON_ORGANIZATION_ROLE)
        return organization_repo.get_persons_with_roles_in_organization(organization_id)
        
    def update_organization_name(self, organization: Organization, data: dict):
        
        if 'name' in data:
            organization.name = data['name']
            organization = self.save_organization(organization)
        
        return organization

    def upload_organization_logo(self, organization: Organization, logo_file: FileStorage):
        
        try:
            # Generate a unique key for the raw logo
            file_extension = logo_file.filename.split('.')[-1] if '.' in logo_file.filename else 'jpeg'
            raw_logo_key = f"organizations/{organization.entity_id}/logo-raw/{uuid.uuid4()}.{file_extension}"
            
            # Save original bucket and set logos bucket
            original_bucket = self.s3_client.bucket_name
            self.s3_client.bucket_name = self.config.AWS_S3_LOGOS_BUCKET_NAME
            
            try:
                # Upload the raw logo to S3 using S3ClientService
                logger.info(f"Uploading raw logo to S3: {raw_logo_key}")
                
                # Read file content into BytesIO
                file_content = BytesIO(logo_file.read())
                
                # Sanitize filename for S3 metadata - remove non-ASCII characters
                sanitized_filename = logo_file.filename.encode('ascii', 'ignore').decode('ascii').strip()
                if not sanitized_filename:
                    sanitized_filename = f"logo.{file_extension}"
                
                self.s3_client.s3.upload_fileobj(
                    Fileobj=file_content,
                    Bucket=self.s3_client.bucket_name,
                    Key=raw_logo_key,
                    ExtraArgs={
                        'ContentType': logo_file.content_type or 'image/jpeg',
                        'Metadata': {
                            'organization_id': organization.entity_id,
                            'original_filename': sanitized_filename
                        }
                    }
                )
                
                logger.info(f"Successfully uploaded raw logo to S3: {raw_logo_key}")
                
            finally:
                # Restore original bucket
                self.s3_client.bucket_name = original_bucket
            
            return True
            
        except Exception as e:
            logger.exception(f"Error uploading logo to S3: {e}")
            return False
    
    def process_subdomain(self, organization: Organization, subdomain: str):

        organization = self.get_organization_by_id(organization.entity_id)
        if not organization:
            return False
        
        message_data = {
            "subdomain": subdomain
        }
        
        return self._send_organization_update_message(organization, message_data)
    
    def update_logo_url(self, organization_id: str, logo_key: str):
        organization = self.get_organization_by_id(organization_id)
        if not organization:
            return None
        
        # Store only the raw S3 path without CloudFront domain
        organization.logo_url = logo_key
        organization = self.save_organization(organization)
        
        return organization
    
    def update_full_domain(self, organization_id: str, full_domain: str):
        organization = self.get_organization_by_id(organization_id)
        if not organization:
            return None
        
        organization.subdomain = full_domain
        organization = self.save_organization(organization)
        
        return organization

    def _send_organization_update_message(self, organization, data=None):
        """Send a message to the organization processor queue using AWS SQS"""
        import boto3
        import json
        
        # Prepare message data
        message_data = {
            "action": "organization_updated",
            "organization_id": organization.entity_id,
            "organization_data": {
                "name": organization.name,
                "subdomain": data['subdomain']
            },
        }
        
        try:
            # Initialize SQS client
            sqs = boto3.client(
                'sqs',
                aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.config.AWS_ACCESS_KEY_SECRET,
                region_name=self.config.AWS_REGION
            )
            
            queue_name = self.config.PREFIXED_ORGANIZATION_PROCESSOR_QUEUE_NAME

            # Get queue URL
            queue_url_response = sqs.get_queue_url(QueueName=queue_name)
            queue_url = queue_url_response['QueueUrl']
            
            message_json = json.dumps(message_data)

            # Send message to SQS
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=message_json
            )
            
            return True
        except Exception as e:
            logger.error(f"Error sending message to SQS: {str(e)}")
            return False


    def get_organization_partners(self, organization_id: str):
        """
        Get all partner organizations associated with the given organization ID.
        """
        return self.organization_repo.get_partner_organizations(organization_id)
    
    def get_next_employee_id(self, organization_id: str) -> str:
        """
        Get the next available employee ID for an organization.
        This method increments the counter and returns a padded 4-digit ID.
        
        Args:
            organization_id: The organization ID
            
        Returns:
            str: Formatted employee ID (e.g., "0001", "0002")
        """
        next_id = self.organization_repo.increment_employee_id_counter(organization_id)
        return f"{next_id:04d}"
    
    def get_next_patient_mrn(self, organization_id: str) -> str:
        """
        Get the next available employee ID for an organization.
        This method increments the counter and returns a padded 4-digit ID.
        
        Args:
            organization_id: The organization ID
            
        Returns:
            str: Formatted employee ID (e.g., "0001", "0002")
        """
        next_id = self.organization_repo.increment_patient_mrn_counter(organization_id)
        return f"{next_id:04d}"