from typing import List
from common.models.patients_file import PatientsFile
from common.repositories.base import BaseRepository

from common.models import PatientsFile, PatientsFileStatusEnum

class PatientsFileRepository(BaseRepository):

    MODEL = PatientsFile
    
    def __init__(self, adapter, message_adapter, message_queue_name, person_id=None):
        super().__init__(adapter, message_adapter, message_queue_name, person_id)

    def get_files_not_in_status(self, organization_id: str, excluded_statuses: list) -> list:
        """
        Get all files for an organization that are NOT in the specified statuses.
        
        Args:
            organization_id (str): The ID of the organization
            excluded_statuses (list): List of statuses to exclude
            
        Returns:
            list: List of PatientFile instances
        """

        included_statuses = [status for status in PatientsFileStatusEnum.values() if status not in excluded_statuses]

        excluded_filter_files = self.get_many({"organization_id": organization_id, "status": included_statuses})
        return excluded_filter_files

    def get_files_by_ids_and_status(self, file_ids: list, organization_id: str, status: str = None) -> List[PatientsFile]:
        """
        Get files by their IDs that are in 'error' status.
        
        Args:
            file_ids (list): List of file entity IDs
            organization_id (str): The ID of the organization
            
        Returns:
            list: List of PatientFile instances in error status
        """
        if not file_ids:
            return []

        if not file_ids:
            return []
        conditions = {'organization_id': organization_id}

        if file_ids:
            conditions['entity_id'] = file_ids
        
        if status:
            conditions['status'] = status


        files = self.get_many(conditions)
        return files

    def get_files_count(self, organization_id: str, status: str = None) -> int:
        """
        Get the count of files for an organization, optionally filtered by status.
        
        Args:
            organization_id (str): The ID of the organization
            status (str, optional): The status to filter by
            
        Returns:
            int: The count of files
        """

        query = "SELECT COUNT(*) FROM patients_file"
        params = []
        conditions = []

        if organization_id:
            conditions.append("organization_id = %s")
            params.append(organization_id)

        if status:
            conditions.append("status = %s")
            params.append(status)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        with self.adapter:
            result = self.adapter.execute_query(query, params if params else None)
        
        if result:
            return result[0]['count']
        
        return None