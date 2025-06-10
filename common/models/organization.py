from rococo.models import Organization as BaseOrganization
from typing import List, Optional
from dataclasses import dataclass

@dataclass(kw_only=True)
class Organization(BaseOrganization):
    logo_url: Optional[str] = None
    subdomain: Optional[str] = None
