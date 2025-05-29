from common.repositories.factory import RepositoryFactory, RepoType
from common.models import Organization
from common.app_logger import logger

class OrganizationService:

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.organization_repo = self.repository_factory.get_repository(RepoType.ORGANIZATION)

    def save_organization(self, organization: Organization):
        organization = self.organization_repo.save(organization)
        return organization

    def get_organization_by_id(self, entity_id: str):
        organization = self.organization_repo.get_one({"entity_id": entity_id})
        return organization

    def get_organizations_with_roles_by_person(self, person_id: str):
        results = self.organization_repo.get_organizations_by_person_id(person_id)
        return results

    def get_persons_with_roles_in_organization(self, organization_id: str):
        organization_repo = self.repository_factory.get_repository(RepoType.PERSON_ORGANIZATION_ROLE)
        return organization_repo.get_persons_with_roles_in_organization(organization_id)
        
    def update_organization(self, organization_id: str, data: dict):
        """Update an organization with the provided data"""
        organization = self.get_organization_by_id(organization_id)

        logger.info(f"Updating organization {organization_id}")
        
        if not organization:
            return None
        
        # Track if we need to send a message
        needs_processing = False
        
        # Update fields
        if 'name' in data:
            organization.name = data['name']
            organization = self.save_organization(organization)

        # Check for logo_url changes
        if 'logo_url' in data and data['logo_url'] and data['logo_url'] != getattr(organization, 'logo_url', None):
            organization.logo_url = data['logo_url']
            organization = self.save_organization(organization)
            logger.info(f"Logo URL updated for organization {organization_id}: {data['logo_url']}")

        if 'full_domain' in data and data['full_domain'] and data['full_domain'] != getattr(organization, 'subdomain', None):
            organization.subdomain = data['full_domain']
            organization = self.save_organization(organization)
            logger.info(f"Subdomain updated for organization {organization_id}: {data['full_domain']}")

        if ('logo_data' in data and data['logo_data']) or ('subdomain' in data and data['subdomain']):
            needs_processing = True
            logger.info(f"Processing logo or subdomain for organization {organization_id}")
        
        # Send message to organization processor if needed
        if needs_processing:
            self._send_organization_update_message(organization, data)
            logger.info(f"Sent organization update message for organization {organization_id}")
        
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
            },
        }
        
        # Include logo data if available
        if data and isinstance(data, dict):
            if 'logo_data' in data:
                message_data["organization_data"]["logo_data"] = data['logo_data']

            if 'subdomain' in data:
                message_data["organization_data"]["subdomain"] = data['subdomain']


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
            
            # Convert message to JSON, handling any serialization issues
            try:
                message_json = json.dumps(message_data)
            except TypeError as e:
                logger.error(f"JSON serialization error: {str(e)}")
                # Remove any problematic fields and try again
                if 'logo_url' in message_data["organization_data"]:
                    del message_data["organization_data"]["logo_url"]
                if 'logo_data' in message_data["organization_data"]:
                    del message_data["organization_data"]["logo_data"]
                message_json = json.dumps(message_data)
            
            # Send message to SQS
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=message_json
            )
            
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error sending message to SQS: {str(e)}")
            return False
