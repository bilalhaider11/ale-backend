from rococo.models import Organization as BaseOrganization
from typing import List, Optional
from dataclasses import dataclass
from common.app_config import config

@dataclass(kw_only=True)
class Organization(BaseOrganization):
    logo_url: Optional[str] = None
    subdomain: Optional[str] = None
    employee_id_counter: Optional[int] = 0
    
    def validate_name(self):
        """
        Truncate organization name to 128 characters.
        """
        if type(self.name) is str:
            self.name = self.name[:128]