from dataclasses import dataclass
from typing import ClassVar
from rococo.models import VersionedModel

@dataclass
class AlertPerson(VersionedModel):
    use_type_checking: ClassVar[bool] = True
    
    alert_id: str = None
    person_id: str = None
    read: bool = False
