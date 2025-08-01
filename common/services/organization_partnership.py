from typing import List
from common.repositories.factory import RepositoryFactory, RepoType
from common.models import OrganizationPartnership, OrganizationPartnershipStatusEnum


class OrganizationPartnershipService:

    def __init__(self, config):
        self.config = config

        self.repository_factory = RepositoryFactory(config)
        self.organization_partnership_repo = self.repository_factory.get_repository(RepoType.ORGANIZATION_PARTNERSHIP)

    @staticmethod
    def get_canonical_pair(org_id_1, org_id_2):
        """
        Returns a tuple of organization IDs in canonical order (smaller ID first). The model is designed to ensure that
        organization_1_id is always less than or equal to organization_2_id.
        Args:
            org_id_1: First organization ID
            org_id_2: Second organization ID
        Returns:
            Tuple of organization IDs in canonical order
        """
        return tuple(sorted([org_id_1, org_id_2]))

    def get_organization_partnership_by_id(self, partnership_id: str) -> OrganizationPartnership:
        """
        Get an organization partnership by its ID.
        Args:
            partnership_id: The ID of the partnership
        Returns:
            OrganizationPartnership object
        """
        partnership = self.organization_partnership_repo.get_one({"entity_id": partnership_id})
        return partnership

    def get_partnership_for_organization(self, organization_partnership_id: str, organization_id: str):
        return self.organization_partnership_repo.get_organization_partnership_by_id(
            organization_partnership_id,
            organization_id
        )

    def save_organization_partnership(self, organization_partnership: OrganizationPartnership):
        organization_partnership.organization_1_id, organization_partnership.organization_2_id = self.get_canonical_pair(
            organization_partnership.organization_1_id,
            organization_partnership.organization_2_id
        )
        organization_partnership = self.organization_partnership_repo.save(organization_partnership)
        return organization_partnership

    def get_all_partnerships_for_organization(self, organization_id: str, status: OrganizationPartnershipStatusEnum = None) -> List[OrganizationPartnership]:
        """
        Get all partnerships for a given organization.
        Args:
            organization_id: The ID of the organization
        Returns:
            List of OrganizationPartnership objects
        """
        partnerships = self.organization_partnership_repo.get_all_organization_partnerships(organization_id, status)
        return partnerships

    def get_active_partner_ids_for_organization(self, organization_id: str) -> List[str]:
        """
        Get IDs of all active partnerships for a given organization.
        Args:
            organization_id: The ID of the organization
        Returns:
            List of organization IDs that are partners with the given organization
        """
        return self.organization_partnership_repo.get_active_partner_ids_for_organization(organization_id)

    def get_organization_partnership(self, org_id_1: str, org_id_2: str) -> OrganizationPartnership:
        """
        Get an existing partnership or create a new one if it doesn't exist.
        Args:
            org_id_1: First organization ID
            org_id_2: Second organization ID
        Returns:
            OrganizationPartnership object
        """
        org_id_1, org_id_2 = self.get_canonical_pair(org_id_1, org_id_2)
        partnership = self.organization_partnership_repo.get_one({
            "organization_1_id": org_id_1,
            "organization_2_id": org_id_2
        })
        return partnership
