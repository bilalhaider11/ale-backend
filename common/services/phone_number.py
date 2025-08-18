from common.app_config import Config
from common.models.phone_number import PhoneNumber
from common.repositories.factory import RepositoryFactory, RepoType

class PhoneNumberService:
    """Service for handling phone number operations."""

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.phone_number_repo = self.repository_factory.get_repository(RepoType.PHONE_NUMBER)

    def save_phone_number(self, phone_number: PhoneNumber):
        phone_number = self.phone_number_repo.save(phone_number)
        return phone_number

    def get_phone_number_by_person_id(self, person_id: str):
        return self.phone_number_repo.get_phone_number_by_person_id(person_id)
