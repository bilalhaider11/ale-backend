from common.repositories.factory import RepositoryFactory, RepoType
from common.models import File


class FileService:

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.file_repo = self.repository_factory.get_repository(RepoType.FILE)

    def save_file(self, file: File) -> File:
        file = self.file_repo.save(file)
        return file

    def get_file_by_id(self, entity_id: str) -> File:
        file = self.file_repo.get_one({'entity_id': entity_id})
        return file
