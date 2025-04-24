from common.repositories.base import BaseRepository
from common.models.person_organization_invite import PersonOrganizationInvitation

class PersonOrganizationInvitationRepository(BaseRepository):
    MODEL = PersonOrganizationInvitation
