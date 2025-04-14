from common.repositories.base import BaseRepository
from common.models.person import Person


class PersonRepository(BaseRepository):
    MODEL = Person
