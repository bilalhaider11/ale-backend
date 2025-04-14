from common.repositories.factory import RepositoryFactory, RepoType
from common.models import Organization


class OrganizationService:

    def __init__(self, config):
        self.config = config
        self.repository_factory = RepositoryFactory(config)
        self.organization_repo = self.repository_factory.get_repository(RepoType.ORGANIZATION)

    def save_organization(self, organization: Organization):
        organization = self.organization_repo.save(organization)
        return organization

    def get_organization_by_id(self, entity_id: str):
        organization = self.organization_repo.get_one({"entity_id": entity_id})
        return organization

    def get_organizations_with_roles_by_person(self, person_id: str):
        results = self.organization_repo.get_organizations_by_person_id(person_id)
        return results
