from typing import List, Dict, Optional
from common.repositories.base import BaseRepository
from common.models.form_data import FormData
from common.app_logger import get_logger

logger = get_logger(__name__)


class FormDataRepository(BaseRepository):
    MODEL = FormData

    def get_form_data_by_person_id(self, person_id: str) -> List[FormData]:
        """
        Get all form data for a specific person.
        
        Args:
            person_id: The person's entity ID
            
        Returns:
            List of FormData objects for the person
        """
        if not person_id:
            raise ValueError("person_id is required")
        return self.get_many({"person_id": person_id})

    def get_form_data_by_person_and_form(self, person_id: str, form_name: str) -> List[FormData]:
        """
        Get all form data for a specific person and form.
        
        Args:
            person_id: The person's entity ID
            form_name: The name of the form
            
        Returns:
            List of FormData objects for the person and form
        """
        if not person_id or not form_name:
            raise ValueError("person_id and form_name are required")
        return self.get_many({
            "person_id": person_id,
            "form_name": form_name
        })

    def get_form_data_by_field(self, person_id: str, form_name: str, field_name: str) -> Optional[FormData]:
        """
        Get a specific form field value for a person.
        
        Args:
            person_id: The person's entity ID
            form_name: The name of the form
            field_name: The name of the field
            
        Returns:
            FormData object if found, None otherwise
        """
        
        return self.get_one({
            "person_id": person_id,
            "form_name": form_name,
            "field_name": field_name
        })

    def save_form_field(self, person_id: str, form_name: str, field_name: str, value: str, changed_by_id: str = None) -> FormData:
        """
        Save a new form field value for a person.
        This method only creates new fields and throws an error if the field already exists.
        
        Args:
            person_id: The person's entity ID
            form_name: The name of the form
            field_name: The name of the field
            value: The field value
            changed_by_id: ID of the user making the change
            
        Returns:
            The saved FormData object
            
        Raises:
            ValueError: If the field already exists for this person and form
        """
        
        # Check if the field already exists
        existing_field = self.get_form_data_by_field(person_id, form_name, field_name)
        if existing_field:
            raise ValueError(f"Form field already exists for person_id={person_id}, form_name={form_name}, field_name={field_name}")
        
        # Create new field
        form_data = FormData(
            person_id=person_id,
            form_name=form_name,
            field_name=field_name,
            value=value
        )
        
        # Set changed_by_id if provided
        if changed_by_id:
            form_data.changed_by_id = changed_by_id
        
        # Validate the form data before saving
        form_data.validate()
        
        return self.save(form_data)




