from dataclasses import dataclass
from typing import Optional, ClassVar
from rococo.models import VersionedModel

@dataclass
class Physician(VersionedModel):
    use_type_checking: ClassVar[bool] = True
    """
    Represents a physician from the CSV import.
    """
    national_provider_identifier: Optional[str] = None
    date_of_birth: Optional[str] = None
    organization_id: Optional[str] = None
    person_id: Optional[str] = None
