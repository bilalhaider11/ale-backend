from common.app_logger import get_logger
from common.repositories.factory import RepositoryFactory, RepoType
from common.models.patients_file import PatientsFile, PatientsFileStatusEnum

logger = get_logger(__name__)


class PatientsFileService:
    
    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.patient_file_repo = self.repository_factory.get_repository(RepoType.PATIENTS_FILE, message_queue_name="")

    def get_by_id(self, entity_id: str, organization_id: str) -> PatientsFile:
        """
        Retrieve a PatientsFile instance by its entity ID.
        
        Args:
            entity_id (str): The unique identifier of the file.
            organization_id (str): The ID of the organization.
        Returns:
            PatientsFile: The file instance if found, otherwise None.
        """
        logger.info(f"Retrieving patient file metadata for entity ID: {entity_id}")
        return self.patient_file_repo.get_one({"entity_id": entity_id, "organization_id": organization_id})

    def get_files(self, organization_id: str, status: str = None) -> list:
        """
        Retrieve all PatientsFile instances for a given organization.
        
        Args:
            organization_id (str): The ID of the organization to filter by.
            status (str, optional): The status to filter files by. If None, retrieves all files.
        
        Returns:
            list: A list of PatientsFile instances.
        """
        logger.info(f"Retrieving patient files for organization: {organization_id} with status: {status}")
        if status:
            return self.patient_file_repo.get_many({"organization_id": organization_id, "status": status})
        return self.patient_file_repo.get_many({"organization_id": organization_id})

    def save_patient_file(self, file_instance: PatientsFile) -> PatientsFile:
        """
        Save a PatientsFile instance to the database.
        
        Args:
            file_instance (PatientsFile): The file metadata to save.
        
        Returns:
            PatientsFile: The saved file instance.
        """
        return self.patient_file_repo.save(file_instance)

    def update_status(self, instance: PatientsFile, status: str) -> PatientsFile:
        """
        Update the status of a PatientsFile instance.
        
        Args:
            instance (PatientsFile): The file instance to update.
            status (str): The new status to set.
        
        Returns:
            PatientsFile: The updated file instance.
        """
        logger.info(f"Updating patient file status to '{status}' for organization: {instance.organization_id}")
        instance.status = status
        return self.patient_file_repo.save(instance)

    def update_record_count(self, instance: PatientsFile, count: int) -> PatientsFile:
        """
        Update the record count of a PatientsFile instance.
        
        Args:
            instance (PatientsFile): The file instance to update.
            count (int): The record count to set.
        
        Returns:
            PatientsFile: The updated file instance.
        """
        logger.info(f"Updating patient record count to {count} for organization: {instance.organization_id}")
        instance.record_count = count
        return self.patient_file_repo.save(instance)

    def set_error(self, instance: PatientsFile, error_message: str) -> PatientsFile:
        """
        Set an error message and update status to 'error' for a PatientsFile instance.
        
        Args:
            instance (PatientsFile): The file instance to update.
            error_message (str): The error message to set.
        
        Returns:
            PatientsFile: The updated file instance.
        """
        logger.info(f"Setting error message for patient file in organization: {instance.organization_id}")
        instance.error_message = error_message
        return self.update_status(instance, PatientsFileStatusEnum.ERROR)

    def poll_files(self, organization_id: str, file_ids: list = None) -> list:
        """
        Return all files not in `done` or `error` status.
        If a file from `file_ids` is in `error` status, it should be included in the response.
        """
        logger.info(f"Polling patient files for organization: {organization_id}")
        
        # Get all files not in 'done' or 'error' status
        files_in_progress = self.patient_file_repo.get_files_not_in_status(
            organization_id=organization_id,
            excluded_statuses=['done']
        )
        
        result_files = files_in_progress.copy()
        
        # If file_ids is provided, also include any files from that list that are in 'error' status
        if file_ids:
            polled_files = self.patient_file_repo.get_files_by_ids_and_status(
                file_ids=file_ids,
                organization_id=organization_id
            )

            # Add error files to result, avoiding duplicates
            existing_ids = {file.entity_id for file in result_files}
            for polled_file in polled_files:
                if polled_file.entity_id not in existing_ids:
                    result_files.append(polled_file)

        logger.info(f"Found {len(result_files)} patient files to poll for organization: {organization_id}")
        return result_files

    def get_files_count(self, organization_id: str, status: str = None) -> int:
        """
        Get the count of PatientsFile instances for a given organization.
        
        Args:
            organization_id (str): The ID of the organization to filter by.
            status (str, optional): The status to filter files by. If None, counts all files.
        
        Returns:
            int: The count of files.
        """
        logger.info(f"Counting patient files for organization: {organization_id} with status: {status}")
        return self.patient_file_repo.get_files_count(organization_id=organization_id, status=status)
    

    def delete_file(self, entity_id: str, organization_id: str) -> None:
        """
        Delete a PatientsFile instance by its entity ID.
        
        Args:
            entity_id (str): The unique identifier of the file to delete.
            organization_id (str): The ID of the organization to filter by.
        """
        logger.info(f"Deleting patient file with entity ID: {entity_id} for organization: {organization_id}")
        file = self.patient_file_repo.get_one({"entity_id": entity_id, "organization_id": organization_id})
        if file:
            self.patient_file_repo.delete(file)
        logger.info(f"Patient file with entity ID: {entity_id} deleted successfully for organization: {organization_id}")
