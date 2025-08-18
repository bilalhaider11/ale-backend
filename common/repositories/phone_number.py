from common.repositories.base import BaseRepository
from common.models import PhoneNumber

class PhoneNumberRepository(BaseRepository):
    MODEL = PhoneNumber
    
    def get_phone_number_by_person_id(self, person_id: str) -> PhoneNumber:
        """
        Get a phone number by person ID.
        
        Args:
            person_id (str): The ID of the person.
            
        Returns:
            PhoneNumber: The phone number if found, otherwise None.
        """
        return self.get_one({"person_id":person_id})
