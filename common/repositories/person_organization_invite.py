from common.repositories.base import BaseRepository
from common.models.person_organization_invite import PersonOrganizationInvitation

class PersonOrganizationInvitationRepository(BaseRepository):
    MODEL = PersonOrganizationInvitation
    
    def delete_invitation(self, entity_id):
        """
        Delete an invitation by entity ID.
        
        Args:
            entity_id (str): The entity ID of the invitation to delete.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        query = f"""
            DELETE FROM person_organization_invitation
            WHERE entity_id = %s
        """
        params = (entity_id,)
        
        with self.adapter:
            self.adapter.execute_query(query, params)
            
        return True
