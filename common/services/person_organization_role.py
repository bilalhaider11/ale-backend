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
    
    def delete_person_organization_role(self, person_organization_role: PersonOrganizationRole):
        person_organization_role = self.person_organization_role_repo.delete(person_organization_role)
        return person_organization_role

    def get_roles_by_person_id(self, person_id: str):
        person_organization_roles = self.person_organization_role_repo.get_many({"person_id": person_id})
        return person_organization_roles
    
    def get_roles_by_orgnization_id(self, organization_id: str):
        person_organization_roles = self.person_organization_role_repo.get_many({"organization_id": organization_id})
        return person_organization_roles
        
    def get_role_of_person_in_organization(self, person_id: str, organization_id: str):
        person_organization_role = self.person_organization_role_repo.get_one({
            "person_id": person_id,
            "organization_id": organization_id
        })
        return person_organization_role

    def get_roles_of_person_in_organization(self, person_id: str, organization_id: str):
        return self.person_organization_role_repo.get_active_roles_for_person_in_organization(person_id, organization_id)

    def get_persons_with_roles_in_organization(self, organization_id: str):
        return self.person_organization_role_repo.get_persons_with_roles_in_organization(organization_id)

    def normalize_roles(self, roles):
        if roles is None:
            return []
        if isinstance(roles, str):
            items = [x.strip() for x in roles.split(",")]
        elif isinstance(roles, (list, tuple, set)):
            items = [str(x).strip() for x in roles]
        else:
            raise ValueError("Invalid roles payload. Must be list or comma-separated string.")

        items = [x.lower() for x in items if x]
        seen, result = set(), []
        for x in items:
            if x not in seen:
                seen.add(x)
                result.append(x)
        return result
    
    def validate_roles(self, roles):
        valid = set(self.person_organization_role_repo.VALID_ROLES)
        invalid = [r for r in roles if r not in valid]
        if invalid:
            raise ValueError(f"Invalid role(s): {', '.join(invalid)}")

    def sync_roles(self, person_id: str, organization_id: str, desired_roles):
        """
        Idempotent sync:
          - For each role in desired -> ensure ACTIVE (reactivate if exists, else create)
          - For each role currently active but not desired -> ensure INACTIVE
        """
        desired = set(self.normalize_roles(desired_roles))
        self.validate_roles(list(desired))

        current = set(self.get_roles_of_person_in_organization(person_id, organization_id))
        to_add = list(desired - current)
        to_remove = list(current - desired)

        for role in to_add:
            person_organization_role = PersonOrganizationRole(
            person_id=person_id,
            organization_id=organization_id,
            role=role,
            active=True
            )
            self.save_person_organization_role(person_organization_role)

        for role in to_remove:
            person_organization_role = self.person_organization_role_repo.get_one({
                "person_id": person_id,
                "organization_id": organization_id,
                "role":role
            })
            self.person_organization_role_repo.delete(person_organization_role)
        
    def delete_roles_for_person_in_organization(self, person_id: str, organization_id: str):
        """
        Delete all roles for a person in an organization.
        
        Args:
            person_id (str): The ID of the person.
            organization_id (str): The ID of the organization.
            
        Returns:
            bool: True if deletion was successful.
        """
        return self.person_organization_role_repo.delete_roles_for_person_in_organization(person_id, organization_id)

