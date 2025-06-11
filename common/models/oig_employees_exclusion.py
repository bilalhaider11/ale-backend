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
    lastname: Optional[str] = None
    firstname: Optional[str] = None
    midname: Optional[str] = None
    busname: Optional[str] = None
    general: Optional[str] = None
    specialty: Optional[str] = None
    upin: Optional[str] = None
    npi: Optional[str] = None
    dob: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    excltype: Optional[str] = None
    excldate: Optional[date] = None
    reindate: Optional[date] = None
    waiverdate: Optional[date] = None
    wvrstate: Optional[str] = None
    
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
        for date_field in ['dob', 'excldate', 'reindate', 'waiverdate']:
            if date_field in processed_data and processed_data[date_field] is not None:
                if isinstance(processed_data[date_field], str):
                    processed_data[date_field] = datetime.strptime(
                        processed_data[date_field], '%Y-%m-%d'
                    ).date()
                elif isinstance(processed_data[date_field], datetime):
                    processed_data[date_field] = processed_data[date_field].date()
        
        return cls(**processed_data)

