from common.repositories.base import BaseRepository
from common.models.login_method import LoginMethod


class LoginMethodRepository(BaseRepository):
    MODEL = LoginMethod
