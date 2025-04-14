from rococo.models import Person as BasePerson
from typing import ClassVar


class Person(BasePerson):
    use_type_checking: ClassVar[bool] = True
