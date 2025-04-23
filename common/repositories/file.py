from common.repositories.base import BaseRepository
from common.models import File


class FileRepository(BaseRepository):
    MODEL = File
