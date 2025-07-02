from typing import List
from common.repositories.base import BaseRepository
from common.models import CurrentEmployeesFile, CurrentEmployeesFileStatusEnum


class CurrentEmployeesFileRepository(BaseRepository):
    MODEL = CurrentEmployeesFile

    def get_files_not_in_status(self, organization_id: str, excluded_statuses: List[str]) -> List[CurrentEmployeesFile]:
        """
        Get all files for an organization that are not in the specified statuses.
        
        Args:
            organization_id (str): The organization ID to filter by.
            excluded_statuses (List[str]): List of statuses to exclude.
        
        Returns:
            List[CurrentEmployeesFile]: List of files not in the excluded statuses.
        """

        included_statuses = [status for status in CurrentEmployeesFileStatusEnum.values() if status not in excluded_statuses]

        excluded_filter_files = self.get_many({"organization_id": organization_id, "status": included_statuses})
        return excluded_filter_files

    def get_files_by_ids_and_status(self, organization_id: str, file_ids: List[str], status: str = None) -> List[CurrentEmployeesFile]:
        """
        Get files by their IDs that have a specific status.
        
        Args:
            file_ids (List[str]): List of file entity IDs.
            status (str): The status to filter by.
            organization_id (str): The organization ID to filter by.
        
        Returns:
            List[CurrentEmployeesFile]: List of files matching the criteria.
        """
        if not file_ids:
            return []
        conditions = {'organization_id': organization_id}

        if file_ids:
            conditions['entity_id'] = file_ids
        
        if status:
            conditions['status'] = status


        files = self.get_many(conditions)
        return files

    def get_files_count(self, organization_id=None, status=None) -> int:
        """
        Get the count of employee exclusion matches in the database.
        Returns:
            int: The number of employee exclusion matches
        """
        query = "SELECT COUNT(*) FROM current_employees_file"
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
        
        print(query)
        if result:
            return result[0]['count']
        
        return None

