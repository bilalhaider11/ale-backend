from common.repositories.base import BaseRepository
from common.models.organization import Organization


class OrganizationRepository(BaseRepository):
    MODEL = Organization

    def get_organizations_by_person_id(self, person_id: str):
        query = """
            SELECT o.*, por.role
            FROM organization AS o
            JOIN person_organization_role AS por
            ON o.entity_id = por.organization_id
            WHERE por.person_id = %s;
        """
        params = (person_id,)

        with self.adapter:
            results = self.adapter.execute_query(query, params)
            return results

    def get_partner_organizations(self, organization_id: str):
        query = """
            SELECT o.*
                FROM organization_partnership op
                JOIN organization o ON o.entity_id = 
                    CASE 
                        WHEN op.organization_1_id = %s THEN op.organization_2_id
                        ELSE op.organization_1_id
                    END
                WHERE 
                    op.active = true
                    AND op.status = 'active'
                    AND (%s = op.organization_1_id OR %s = op.organization_2_id)
        """
        params = (organization_id, organization_id, organization_id)

        with self.adapter:
            results = self.adapter.execute_query(query, params)
        return results if results else []
    
    def increment_employee_id_counter(self, organization_id: str) -> int:
        """
        Atomically increment and return the employee_id_counter for an organization.
        This uses a database transaction to ensure thread-safety.
        
        Args:
            organization_id: The organization ID
            
        Returns:
            int: The next employee ID counter value
        """
        update_query = """
            UPDATE organization 
            SET employee_id_counter = COALESCE(employee_id_counter, 0) + 1
            WHERE entity_id = %s
        """
        
        select_query = """
            SELECT employee_id_counter 
            FROM organization 
            WHERE entity_id = %s
        """
        
        with self.adapter:
            # Perform the update
            self.adapter.execute_query(update_query, (organization_id,))
            # Fetch the updated value
            result = self.adapter.execute_query(select_query, (organization_id,))
        
        if result and len(result) > 0:
            return result[0]['employee_id_counter']
        
        # If no result, the organization might not exist
        return 1
    
    
    def increment_patient_mrn_counter(self, organization_id: str) -> int:
        """
        Atomically increment and return the employee_id_counter for an organization.
        This uses a database transaction to ensure thread-safety.
        
        Args:
            organization_id: The organization ID
            
        Returns:
            int: The next employee ID counter value
        """
        update_query = """
            UPDATE organization 
            SET patient_mrn_counter = COALESCE(patient_mrn_counter, 0) + 1
            WHERE entity_id = %s
        """
        
        select_query = """
            SELECT patient_mrn_counter 
            FROM organization 
            WHERE entity_id = %s
        """
        
        with self.adapter:
            # Perform the update
            self.adapter.execute_query(update_query, (organization_id,))
            # Fetch the updated value
            result = self.adapter.execute_query(select_query, (organization_id,))
        
        if result and len(result) > 0:
            return result[0]['patient_mrn_counter']
        
        # If no result, the organization might not exist
        return 1