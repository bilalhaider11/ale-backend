from common.repositories.factory import RepositoryFactory, RepoType
from common.models import LoginMethod
from common.models.login_method import LoginMethodType


class LoginMethodService:

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.login_method_repo = self.repository_factory.get_repository(RepoType.LOGIN_METHOD)

    def save_login_method(self, login_method: LoginMethod):
        login_method = self.login_method_repo.save(login_method)
        return login_method

    def get_login_method_by_email_id(self, email_id: str):
        login_method = self.login_method_repo.get_one({"email_id": email_id, "method_type": LoginMethodType.EMAIL_PASSWORD})
        return login_method
    
    def get_login_method_by_id(self, entity_id: str):
        login_method = self.login_method_repo.get_one({"entity_id": entity_id})
        return login_method

    def update_password(self, login_method: LoginMethod, password: str) -> LoginMethod:
        login_method.password = password
        return self.login_method_repo.save(login_method)
