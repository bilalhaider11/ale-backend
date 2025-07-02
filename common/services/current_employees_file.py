from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.current_employees_file import CurrentEmployeesFile, CurrentEmployeesFileStatusEnum

logger = get_logger(__name__)


class CurrentEmployeesFileService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.current_employees_file_repo = self.repository_factory.get_repository(RepoType.CURRENT_EMPLOYEES_FILE, message_queue_name="")

    def get_by_id(self, entity_id: str, organization_id: str) -> CurrentEmployeesFile:
        """
        Retrieve a CurrentEmployeesFile instance by its entity ID.
        
        Args:
            entity_id (str): The unique identifier of the file.
        Returns:
            CurrentEmployeesFile: The file instance if found, otherwise None.
        """
        logger.info(f"Retrieving file metadata for entity ID: {entity_id}")
        return self.current_employees_file_repo.get_one({"entity_id": entity_id, "organization_id": organization_id})

    def get_files(self, organization_id: str, status: str = None) -> list:
        """
        Retrieve all CurrentEmployeesFile instances for a given organization.
        
        Args:
            organization_id (str): The ID of the organization to filter by.
            status (str, optional): The status to filter files by. If None, retrieves all files.
        
        Returns:
            list: A list of CurrentEmployeesFile instances.
        """
        logger.info(f"Retrieving files for organization: {organization_id} with status: {status}")
        if status:
            return self.current_employees_file_repo.get_many({"organization_id": organization_id, "status": status})
        return self.current_employees_file_repo.get_many({"organization_id": organization_id})

    def save_employees_file(self, file_instance: CurrentEmployeesFile) -> CurrentEmployeesFile:
        """
        Save a CurrentEmployeesFile instance to the database.
        
        Args:
            file_instance (CurrentEmployeesFile): The file metadata to save.
        
        Returns:
            CurrentEmployeesFile: The saved file instance.
        """
        logger.info(f"Saving file metadata for organization: {file_instance.organization_id}")
        return self.current_employees_file_repo.save(file_instance)

    def update_status(self, instance: CurrentEmployeesFile, status: str) -> CurrentEmployeesFile:
        """
        Update the status of a CurrentEmployeesFile instance.
        
        Args:
            instance (CurrentEmployeesFile): The file instance to update.
            status (str): The new status to set.
        
        Returns:
            CurrentEmployeesFile: The updated file instance.
        """
        logger.info(f"Updating file status to '{status}' for organization: {instance.organization_id}")
        instance.status = status
        return self.current_employees_file_repo.save(instance)

    def update_record_count(self, instance: CurrentEmployeesFile, count: int) -> CurrentEmployeesFile:
        """
        Update the record count of a CurrentEmployeesFile instance.
        
        Args:
            instance (CurrentEmployeesFile): The file instance to update.
            count (int): The record count to set.
        
        Returns:
            CurrentEmployeesFile: The updated file instance.
        """
        logger.info(f"Updating record count to {count} for organization: {instance.organization_id}")
        instance.record_count = count
        return self.current_employees_file_repo.save(instance)

    def set_error(self, instance: CurrentEmployeesFile, error_message: str) -> CurrentEmployeesFile:
        """
        Set an error message and update status to 'error' for a CurrentEmployeesFile instance.
        
        Args:
            instance (CurrentEmployeesFile): The file instance to update.
            error_message (str): The error message to set.
        
        Returns:
            CurrentEmployeesFile: The updated file instance.
        """
        logger.info(f"Setting error message for organization: {instance.organization_id}")
        instance.error_message = error_message
        return self.update_status(instance, CurrentEmployeesFileStatusEnum.ERROR)

    def poll_files(self, organization_id: str, file_ids: list = None) -> list:
        """
        Return all files not in `done` or `error` status.
        If a file from `file_ids` is in `error` status, it should be included in the response.
        """
        logger.info(f"Polling files for organization: {organization_id}")
        
        # Get all files not in 'done' or 'error' status
        files_in_progress = self.current_employees_file_repo.get_files_not_in_status(
            organization_id=organization_id,
            excluded_statuses=['done']
        )
        
        result_files = files_in_progress.copy()
        
        # If file_ids is provided, also include any files from that list that are in 'error' status
        if file_ids:
            polled_files = self.current_employees_file_repo.get_files_by_ids_and_status(
                file_ids=file_ids,
                organization_id=organization_id
            )

            # Add error files to result, avoiding duplicates
            existing_ids = {file.entity_id for file in result_files}
            for polled_file in polled_files:
                if polled_file.entity_id not in existing_ids:
                    result_files.append(polled_file)

        logger.info(f"Found {len(result_files)} files to poll for organization: {organization_id}")
        return result_files

    def get_files_count(self, organization_id: str, status: str = None) -> int:
        """
        Get the count of CurrentEmployeesFile instances for a given organization.
        
        Args:
            organization_id (str): The ID of the organization to filter by.
            status (str, optional): The status to filter files by. If None, counts all files.
        
        Returns:
            int: The count of files.
        """
        logger.info(f"Counting files for organization: {organization_id} with status: {status}")
        return self.current_employees_file_repo.get_files_count(organization_id=organization_id, status=status)
    

    def delete_file(self, entity_id: str, organization_id: str) -> None:
        """
        Delete a CurrentEmployeesFile instance by its entity ID.
        
        Args:
            entity_id (str): The unique identifier of the file to delete.
            organization_id (str): The ID of the organization to filter by.
        """
        logger.info(f"Deleting file with entity ID: {entity_id} for organization: {organization_id}")
        file = self.current_employees_file_repo.get_one({"entity_id": entity_id, "organization_id": organization_id})
        if file:
            self.current_employees_file_repo.delete(file)
        logger.info(f"File with entity ID: {entity_id} deleted successfully for organization: {organization_id}")
