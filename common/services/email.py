from common.repositories.factory import RepositoryFactory, RepoType
from common.models import Email


class EmailService:

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.email_repo = self.repository_factory.get_repository(RepoType.EMAIL)

    def save_email(self, email: Email):
        email = self.email_repo.save(email)
        return email

    def get_email_by_email_address(self, email_address: str):
        email = self.email_repo.get_one({'email': email_address})
        return email

    def get_email_by_id(self, entity_id: str):
        email = self.email_repo.get_one({'entity_id': entity_id})
        return email

    def verify_email(self, email: Email) -> Email:
        email.is_verified = True
        return self.save_email(email)
