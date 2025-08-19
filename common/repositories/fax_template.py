from typing import List, Optional
from common.models.fax_template import FaxTemplate
from common.repositories.base import BaseRepository
from common.app_logger import logger


class FaxTemplateRepository(BaseRepository):
    MODEL = FaxTemplate

    def __init__(self, adapter, message_adapter, message_queue_name, person_id):
        super().__init__(adapter, message_adapter, message_queue_name, person_id)

    def get_by_organization_id(self, organization_id: str) -> List[FaxTemplate]:
        """
        Get all active fax templates for a specific organization.
        
        Args:
            organization_id: The organization ID to filter by
            
        Returns:
            List of active fax templates for the organization, sorted by name
            
        Raises:
            Exception: If database query fails
        """
        if not organization_id:
            logger.warning("get_by_organization_id called with empty organization_id")
            return []
            
        query = """
            SELECT * FROM fax_template 
            WHERE organization_id = %s AND active = TRUE 
            ORDER BY name ASC
        """
        try:
            with self.adapter:
                results = self.adapter.execute_query(query, (organization_id,))
            return [self.MODEL(**result) for result in results]
        except Exception as e:
            logger.error(f"Error fetching fax templates for organization {organization_id}: {str(e)}")
            raise

    def get_by_id_and_organization(self, entity_id: str, organization_id: str) -> Optional[FaxTemplate]:
        """
        Get a specific fax template by ID and organization.
        
        Args:
            entity_id: The template entity ID
            organization_id: The organization ID
            
        Returns:
            The fax template if found, None otherwise
            
        Raises:
            Exception: If database query fails
        """
        if not entity_id or not organization_id:
            logger.warning("get_by_id_and_organization called with empty entity_id or organization_id")
            return None
            
        query = """
            SELECT * FROM fax_template 
            WHERE entity_id = %s AND organization_id = %s AND active = TRUE
        """
        try:
            with self.adapter:
                results = self.adapter.execute_query(query, (entity_id, organization_id))
            if results:
                return self.MODEL(**results[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching fax template {entity_id} for organization {organization_id}: {str(e)}")
            raise

    def name_exists_for_organization(self, name: str, organization_id: str, exclude_entity_id: str = None) -> bool:
        """
        Check if a template name already exists for an organization.
        
        Args:
            name: The template name to check
            organization_id: The organization ID
            exclude_entity_id: Optional entity ID to exclude from the check (for updates)
            
        Returns:
            True if name exists, False otherwise
            
        Raises:
            Exception: If database query fails
        """
        if not name or not organization_id:
            logger.warning("name_exists_for_organization called with empty name or organization_id")
            return False
            
        if exclude_entity_id:
            query = """
                SELECT EXISTS(
                    SELECT 1 FROM fax_template 
                    WHERE LOWER(name) = LOWER(%s) AND organization_id = %s AND active = TRUE 
                    AND entity_id != %s
                ) as exists
            """
            params = (name, organization_id, exclude_entity_id)
        else:
            query = """
                SELECT EXISTS(
                    SELECT 1 FROM fax_template 
                    WHERE LOWER(name) = LOWER(%s) AND organization_id = %s AND active = TRUE
                ) as exists
            """
            params = (name, organization_id)
            
        try:
            with self.adapter:
                results = self.adapter.execute_query(query, params)
            if results:
                return results[0]['exists']
            return False
        except Exception as e:
            logger.error(f"Error checking if name '{name}' exists for organization {organization_id}: {str(e)}")
            raise

    def delete_template(self, entity_id: str, organization_id: str) -> bool:
        """
        Soft delete a fax template by setting active = FALSE.
        
        Args:
            entity_id: The template entity ID
            organization_id: The organization ID
            
        Returns:
            True if template was deleted, False otherwise
            
        Raises:
            Exception: If database query fails
        """
        if not entity_id or not organization_id:
            logger.warning("delete_template called with empty entity_id or organization_id")
            return False
            
        query = """
            UPDATE fax_template 
            SET active = FALSE 
            WHERE entity_id = %s AND organization_id = %s AND active = TRUE
        """
        try:
            with self.adapter:
                self.adapter.execute_query(query, (entity_id, organization_id))
                return True
        except Exception as e:
            logger.error(f"Error deleting fax template {entity_id} for organization {organization_id}: {str(e)}")
            return False

    def get_template_count_by_organization(self, organization_id: str) -> int:
        """
        Get the count of active fax templates for an organization.
        
        Args:
            organization_id: The organization ID to filter by
            
        Returns:
            Number of active fax templates for the organization
            
        Raises:
            Exception: If database query fails
        """
        if not organization_id:
            logger.warning("get_template_count_by_organization called with empty organization_id")
            return 0
            
        query = """
            SELECT COUNT(*) as count FROM fax_template 
            WHERE organization_id = %s AND active = TRUE
        """
        try:
            with self.adapter:
                results = self.adapter.execute_query(query, (organization_id,))
            if results:
                return results[0]['count']
            return 0
        except Exception as e:
            logger.error(f"Error counting fax templates for organization {organization_id}: {str(e)}")
            raise

    def search_templates_by_name(self, organization_id: str, name_pattern: str) -> List[FaxTemplate]:
        """
        Search for fax templates by name pattern within an organization.
        
        Args:
            organization_id: The organization ID to filter by
            name_pattern: The name pattern to search for (case-insensitive)
            
        Returns:
            List of matching fax templates, sorted by name
            
        Raises:
            Exception: If database query fails
        """
        if not organization_id or not name_pattern:
            logger.warning("search_templates_by_name called with empty organization_id or name_pattern")
            return []
            
        query = """
            SELECT * FROM fax_template 
            WHERE organization_id = %s AND active = TRUE 
            AND LOWER(name) LIKE LOWER(%s)
            ORDER BY name ASC
        """
        try:
            with self.adapter:
                results = self.adapter.execute_query(query, (organization_id, f"%{name_pattern}%"))
            return [self.MODEL(**result) for result in results]
        except Exception as e:
            logger.error(f"Error searching fax templates for organization {organization_id} with pattern '{name_pattern}': {str(e)}")
            raise
