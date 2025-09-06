from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, ClassVar
from enum import IntEnum
from rococo.models import VersionedModel

class AlertLevelEnum(IntEnum):
    INFO = 0
    WARNING = 1
    CRITICAL = 2
    
    @classmethod
    def values(cls):
        return [item.value for item in cls]

class AlertStatusEnum(IntEnum):
    OPEN = 0
    IN_PROGRESS = 1
    ADDRESSED = 2
    
    @classmethod
    def values(cls):
        return [item.value for item in cls]

@dataclass
class Alert(VersionedModel):
    use_type_checking: ClassVar[bool] = True
    
    organization_id: str = None
    level: int = None
    area: str = None
    message: str = None
    status: int = field(default=AlertStatusEnum.OPEN)
    assigned_to_id: Optional[str] = None
    handled_at_start: Optional[datetime] = None
    handled_at_end: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    def validate_level(self):
        # Check if level is a valid integer for AlertLevelEnum
        valid_levels = [item.value for item in AlertLevelEnum]
        if self.level not in valid_levels:
            raise ValueError(f"Invalid alert level: {self.level}. Must be one of {valid_levels}")
    
    def validate_status(self):
        # Check if status is a valid integer for AlertStatusEnum
        valid_statuses = [item.value for item in AlertStatusEnum]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid alert status: {self.status}. Must be one of {valid_statuses}")
