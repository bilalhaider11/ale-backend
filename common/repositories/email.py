from common.repositories.base import BaseRepository
from common.models.email import Email


class EmailRepository(BaseRepository):
    MODEL = Email
