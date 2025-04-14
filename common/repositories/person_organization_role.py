from common.repositories.base import BaseRepository
from common.models.person_organization_role import PersonOrganizationRole


class PersonOrganizationRoleRepository(BaseRepository):
    MODEL = PersonOrganizationRole
