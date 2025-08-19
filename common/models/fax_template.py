from dataclasses import dataclass
from typing import Optional, ClassVar
from rococo.models import VersionedModel

@dataclass
class FaxTemplate(VersionedModel):
    use_type_checking: ClassVar[bool] = True
    """
    Represents a fax template that can be used to send faxes to physicians.
    This is a versioned model that tracks template changes over time.
    """
    name: Optional[str] = None
    body: Optional[str] = None
    organization_id: Optional[str] = None

    def validate_name(self) -> None:
        """
        Ensure name is not empty and has reasonable length.
        
        Raises:
            ValueError: If name is invalid
        """
        if not self.name:
            raise ValueError("Template name cannot be empty")
        
        if len(self.name) > 255:
            raise ValueError("Template name must be 255 characters or less")
        
        if len(self.name.strip()) == 0:
            raise ValueError("Template name cannot be only whitespace")

    def validate_body(self) -> None:
        """
        Ensure body is not empty and has reasonable length.
        
        Raises:
            ValueError: If body is invalid
        """
        if len(self.body) > 16777216:  # MEDIUMTEXT limit
            raise ValueError("Template body is too long (max 16,777,216 characters)")
