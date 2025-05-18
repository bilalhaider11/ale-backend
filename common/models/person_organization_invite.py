from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from rococo.models.versioned_model import VersionedModel

@dataclass
class PersonOrganizationInvitation(VersionedModel):
    """
    Invitation of a Person (by email) to join an Organization,
    with status tracking and acceptance metadata.
    """
    organization_id: str = None
    invitee_id: str = None
    email: str = None
    roles: str = None
    token: str = None
    status: str = 'pending'
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    accepted_on: Optional[datetime] = None