from dataclasses import dataclass
from typing import Optional, ClassVar
import re
from rococo.models import VersionedModel
from common.constants.form_names import FORM_NAMES


@dataclass
class FormData(VersionedModel):
    use_type_checking: ClassVar[bool] = True
    """
    Represents a form field value for a specific person and form.
    This is a versioned model that tracks form data over time.
    """
    person_id: Optional[str] = None
    form_name: Optional[str] = None
    field_name: Optional[str] = None
    value: Optional[str] = None

    # Compile regex pattern once for better performance
    _FORM_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\s]+$')

    def validate_form_name(self) -> None:
        """
        Ensure form_name is from the predefined list of valid form names.
        
        Raises:
            ValueError: If form name is invalid
        """
        if not self.form_name:
            raise ValueError("Form name cannot be empty")
        
        if len(self.form_name) > 32:
            raise ValueError("Form name must be 32 characters or less")
        
        # Check for valid characters using pre-compiled regex
        if not self._FORM_NAME_PATTERN.match(self.form_name):
            raise ValueError("Form name can only contain letters, numbers, spaces, underscores, and hyphens")
        
        # Validate against known form constants
        if self.form_name not in FORM_NAMES:
            valid_forms = ', '.join(sorted(FORM_NAMES))
            raise ValueError(f"Form name '{self.form_name}' is not valid. Valid forms: {valid_forms}")

    def validate_field_name(self) -> None:
        """
        Ensure field_name is not empty and reasonable length.
        
        Raises:
            ValueError: If field name is invalid
        """
        if not self.field_name or not self.field_name.strip():
            raise ValueError("Field name cannot be empty")
        
        if len(self.field_name) > 128:
            raise ValueError("Field name must be 128 characters or less")

    def validate_value(self) -> None:
        """
        Ensure value is stored as string and handle None values.
        """
        if self.value is not None:
            self.value = str(self.value)
        else:
            self.value = ""

    def validate(self) -> None:
        """
        Validate all fields of the form data.
        
        Raises:
            ValueError: If any validation fails
        """
        self.validate_form_name()
        self.validate_field_name()
        self.validate_value()
