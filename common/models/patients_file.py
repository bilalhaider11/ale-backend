from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum
from typing import Optional, ClassVar
from rococo.models import VersionedModel


class PatientsFileStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    IMPORTED = 'imported'
    DONE = "done"
    ERROR = "error"

    def __repr__(self):
        return str(self.value)

    @classmethod
    def values(cls):
        return [v.value for v in cls.__members__.values() if isinstance(v, cls)]


@dataclass(kw_only=True)
class PatientsFile(VersionedModel):
    use_type_checking: ClassVar[bool] = True

    organization_id: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    s3_key: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    uploaded_by: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    record_count: Optional[int] = None
