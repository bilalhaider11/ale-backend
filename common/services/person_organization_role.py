from common.repositories.factory import RepositoryFactory, RepoType
from common.models import PersonOrganizationRole


class PersonOrganizationRoleService:

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.person_organization_role_repo = self.repository_factory.get_repository(RepoType.PERSON_ORGANIZATION_ROLE)

    def save_person_organization_role(self, person_organization_role: PersonOrganizationRole):
        person_organization_role = self.person_organization_role_repo.save(person_organization_role)
        return person_organization_role

    def get_roles_by_person_id(self, person_id: str):
        person_organization_roles = self.person_organization_role_repo.get_many({"person_id": person_id})
        
    def get_role_of_person_in_organization(self, person_id: str, organization_id: str):
        person_organization_role = self.person_organization_role_repo.get_one({
            "person_id": person_id,
            "organization_id": organization_id
        })
        return person_organization_role