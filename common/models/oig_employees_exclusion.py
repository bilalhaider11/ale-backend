from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import date, datetime

@dataclass(kw_only=True)
class OigEmployeesExclusion:
    """
    Represents a single record from the OIG LEIE database CSV.
    This table is designed to be truncated and re-populated on each import.
    """
    id: int = None
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    business_name: Optional[str] = None
    general: Optional[str] = None
    specialty: Optional[str] = None
    upin: Optional[str] = None
    npi: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    exclusion_type: Optional[str] = None
    exclusion_date: Optional[date] = None
    reinstatement_date: Optional[date] = None
    waiver_date: Optional[date] = None
    waiver_state: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OigEmployeesExclusion':
        """
        Create an OigEmployeesExclusion instance from a dictionary.
        Handles date field conversions from string representation.
        
        Args:
            data: Dictionary containing OIG exclusion data
            
        Returns:
            An OigEmployeesExclusion instance
        """
        # Make a copy to avoid modifying the input
        processed_data = dict(data)
        
        # Convert date strings to date objects if they exist and aren't None
        for date_field in ['date_of_birth', 'exclusion_date', 'reinstatement_date', 'waiver_date']:
            if date_field in processed_data and processed_data[date_field] is not None:
                if isinstance(processed_data[date_field], str):
                    processed_data[date_field] = datetime.strptime(
                        processed_data[date_field], '%Y-%m-%d'
                    ).date()
                elif isinstance(processed_data[date_field], datetime):
                    processed_data[date_field] = processed_data[date_field].date()
        
        return cls(**processed_data)


    def as_dict(self):
        """
        Convert the CurrentEmployee instance to a dictionary.
        
        Returns:
            dict: Dictionary representation of the CurrentEmployee instance
        """
        return {field.name: getattr(self, field.name) for field in self.__dataclass_fields__.values() if getattr(self, field.name) is not None}
