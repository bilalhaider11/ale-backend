from dataclasses import dataclass
from datetime import date
from typing import Optional, ClassVar
from rococo.models import VersionedModel


@dataclass
class EmployeeExclusionMatch(VersionedModel):
    use_type_checking: ClassVar[bool] = True

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
