from common.models.alert import Alert
from common.repositories.base import BaseRepository

class AlertRepository(BaseRepository):
    MODEL = Alert