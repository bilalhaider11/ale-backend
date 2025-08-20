from dataclasses import dataclass
from typing import ClassVar
from rococo.models import VersionedModel

@dataclass
class PhoneNumber(VersionedModel):
    use_type_checking: ClassVar[bool] = True

    phone: str = None
    person_id: str = None