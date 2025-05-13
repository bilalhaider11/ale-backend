from rococo.models import VersionedModel
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from common.constants.content_types import TEXTRACT_ACCEPTED_CONTENT_TYPES, CONVERTABLE_CONTENT_TYPES


class FileStatusEnum(str, Enum):
    UPLOADED = "uploaded"
    EXTRACTED = "extracted"
    NOT_SUPPORTED = "not_supported"
    CONVERTED = "converted"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ERROR = "error"

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.ordered_values().index(self.value) > self.ordered_values().index(other.value)
        return NotImplemented

    @classmethod
    def ordered_values(cls):
        return [v.value for v in cls.__dict__.values() if isinstance(v, cls)]



@dataclass(repr=False)
class File(VersionedModel):
    organization_id: str = None
    person_id: str = None
    filename: str = None
    s3_key: str = None
    content_type: str = None
    size_bytes: int = None
    uploaded_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_converted: bool = False
    source_file_id: str = None
    status: FileStatusEnum = None

    @property
    def is_system(self):
        return self.person_id is None

    @property
    def ready_to_process(self):
        if self.content_type in TEXTRACT_ACCEPTED_CONTENT_TYPES and self.status >= FileStatusEnum.UPLOADED:
            return True
        elif self.content_type in CONVERTABLE_CONTENT_TYPES and self.status >= FileStatusEnum.CONVERTED:
            return True
        return False
