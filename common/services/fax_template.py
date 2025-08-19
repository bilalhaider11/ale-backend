from typing import List, Optional
from common.models.fax_template import FaxTemplate
from common.repositories.factory import RepoType, RepositoryFactory
from common.app_config import config
from common.app_logger import logger


class FaxTemplateService:
    """
    Service for managing fax template operations.
    """

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.fax_template_repo = self.repository_factory.get_repository(RepoType.FAX_TEMPLATE)

    def get_templates_by_organization(self, organization_id: str) -> List[FaxTemplate]:
        """
        Get all active fax templates for an organization.
        
        Args:
            organization_id: The organization ID
            
        Returns:
            List of active fax templates
        """
        try:
            return self.fax_template_repo.get_by_organization_id(organization_id)
        except Exception as e:
            logger.error(f"Service error getting templates for organization {organization_id}: {str(e)}")
            raise

    def get_template_by_id(self, entity_id: str, organization_id: str) -> Optional[FaxTemplate]:
        """
        Get a specific fax template by ID and organization.
        
        Args:
            entity_id: The template entity ID
            organization_id: The organization ID
            
        Returns:
            The fax template if found, None otherwise
        """
        try:
            return self.fax_template_repo.get_by_id_and_organization(entity_id, organization_id)
        except Exception as e:
            logger.error(f"Service error getting template {entity_id} for organization {organization_id}: {str(e)}")
            raise

    def get_template_count_by_organization(self, organization_id: str) -> int:
        """
        Get the count of active fax templates for an organization.
        
        Args:
            organization_id: The organization ID
            
        Returns:
            Number of active fax templates
        """
        try:
            return self.fax_template_repo.get_template_count_by_organization(organization_id)
        except Exception as e:
            logger.error(f"Service error counting templates for organization {organization_id}: {str(e)}")
            raise

    def search_templates_by_name(self, organization_id: str, name_pattern: str) -> List[FaxTemplate]:
        """
        Search for fax templates by name pattern within an organization.
        
        Args:
            organization_id: The organization ID
            name_pattern: The name pattern to search for (case-insensitive)
            
        Returns:
            List of matching fax templates
        """
        try:
            return self.fax_template_repo.search_templates_by_name(organization_id, name_pattern)
        except Exception as e:
            logger.error(f"Service error searching templates for organization {organization_id} with pattern '{name_pattern}': {str(e)}")
            raise

    def create_template(self, template: FaxTemplate) -> FaxTemplate:
        """
        Create a new fax template.
        
        Args:
            template: The fax template to create
            
        Returns:
            The created fax template
            
        Raises:
            ValueError: If template validation fails
        """
        try:
            # Validate the template
            template.validate_name()
            template.validate_body()
            
            # Check if template with same name already exists for this organization
            if self.fax_template_repo.name_exists_for_organization(template.name, template.organization_id):
                raise ValueError(f"Template with name '{template.name}' already exists.")
            
            return self.fax_template_repo.save(template)
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Service error creating template: {str(e)}")
            raise

    def update_template(self, template: FaxTemplate) -> FaxTemplate:
        """
        Update an existing fax template.
        
        Args:
            template: The fax template to update
            
        Returns:
            The updated fax template
            
        Raises:
            ValueError: If template validation fails or template doesn't exist
        """
        try:
            # Validate the template
            template.validate_name()
            template.validate_body()
            
            # Check if template exists
            existing_template = self.get_template_by_id(template.entity_id, template.organization_id)
            if not existing_template:
                raise ValueError(f"Template with ID {template.entity_id} not found")
            
            # Check if template with same name already exists (excluding current template)
            if self.fax_template_repo.name_exists_for_organization(template.name, template.organization_id, template.entity_id):
                raise ValueError(f"Template with name '{template.name}' already exists.")
            
            return self.fax_template_repo.save(template)
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Service error updating template {template.entity_id}: {str(e)}")
            raise

    def delete_template(self, entity_id: str, organization_id: str) -> bool:
        """
        Delete a fax template.
        
        Args:
            entity_id: The template entity ID
            organization_id: The organization ID
            
        Returns:
            True if template was deleted, False otherwise
        """
        try:
            # Check if template exists before attempting to delete
            existing_template = self.get_template_by_id(entity_id, organization_id)
            if not existing_template:
                logger.warning(f"Attempted to delete non-existent template {entity_id} for organization {organization_id}")
                return False
            
            return self.fax_template_repo.delete_template(entity_id, organization_id)
        except Exception as e:
            logger.error(f"Service error deleting template {entity_id}: {str(e)}")
            raise
