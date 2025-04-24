from collections import OrderedDict

from common.repositories.base import BaseRepository
from common.models.person_organization_role import PersonOrganizationRole


class PersonOrganizationRoleRepository(BaseRepository):
    MODEL = PersonOrganizationRole

    # Set of valid roles for validation
    VALID_ROLES = {
        "admin",
        "intake",
        "scheduler",
        "billing",
        "payroll",
        "rn",
        "auditor",
        "caregiver"
    }

    def __init__(self, adapter, message_adapter, message_queue_name, person_id):
        super().__init__(adapter, message_adapter, message_queue_name, person_id)

    def get_persons_with_roles_in_organization(self, organization_id: str):
        """
        Fetch all people in the given organization along with their roles.
        Only roles in VALID_ROLES are returned, and people are sorted
        by their latest role‐change timestamp (changed_on DESC).
        """
        # Build an IN‑clause with placeholders for valid roles
        placeholders = ", ".join(["%s"] * len(self.VALID_ROLES))

        query = f"""
            SELECT
                p.entity_id   AS person_id,
                p.first_name,
                p.last_name,
                por.role,
                por.changed_on
            FROM person_organization_role AS por
            JOIN person AS p
              ON por.person_id = p.entity_id
            WHERE por.organization_id = %s
              AND por.role IN ({placeholders})
            ORDER BY por.changed_on DESC;
        """

        # First parameter is org id, then each role value
        params = (organization_id, *self.VALID_ROLES)

        with self.adapter:
            rows = self.adapter.execute_query(query, params)

        # Group by person, preserving the SQL order (latest changed_on first)
        persons = OrderedDict()
        for r in rows:
            pid = r["person_id"]
            if pid not in persons:
                persons[pid] = {
                    "id": pid,
                    "first_name": r["first_name"],
                    "last_name": r["last_name"],
                    "roles": []
                }
            # Since SQL only returned VALID_ROLES, no need to re‑validate here
            persons[pid]["roles"].append(r["role"])

        # Return as a list in the same order we inserted (most recent first)
        return list(persons.values())

    def get_roles_for_person_in_organization(self, person_id: str, organization_id: str):
        """
        Fetch all role names for a specific person in a given organization.
        Only roles in VALID_ROLES are returned.
        """
        # Build an IN-clause with placeholders for valid roles
        placeholders = ", ".join(["%s"] * len(self.VALID_ROLES))

        query = f"""
            SELECT
                por.role
            FROM person_organization_role AS por
            WHERE por.person_id = %s
              AND por.organization_id = %s
              AND por.role IN ({placeholders})
            ORDER BY por.changed_on DESC;
        """

        # Parameters: person_id, organization_id, then each role value
        params = (person_id, organization_id, *self.VALID_ROLES)

        with self.adapter:
            rows = self.adapter.execute_query(query, params)

        # Extract role names
        roles = [row["role"] for row in rows]
        return roles