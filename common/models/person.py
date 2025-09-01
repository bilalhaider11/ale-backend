from rococo.models import Person as BasePerson
from typing import ClassVar, Optional
from dataclasses import dataclass

@dataclass
class Person(BasePerson):
    use_type_checking: ClassVar[bool] = True
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    
    def validate_first_name(self):
        """
        Truncate first name to 128 characters.
        """
        if type(self.first_name) is str:
            self.first_name = self.first_name[:128]
    
    def validate_last_name(self):
        """
        Truncate last name to 128 characters.
        """
        if type(self.last_name) is str:
            self.last_name = self.last_name[:128]
