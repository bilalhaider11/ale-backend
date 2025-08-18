from collections import OrderedDict

from common.repositories.base import BaseRepository
from common.models.person_organization_role import PersonOrganizationRole, PersonOrganizationRoleEnum
from collections import defaultdict

class PersonOrganizationRoleRepository(BaseRepository):
    MODEL = PersonOrganizationRole

    # Set of valid roles for validation
    VALID_ROLES = PersonOrganizationRoleEnum.valid_values()

    def __init__(self, adapter, message_adapter, message_queue_name, person_id):
        super().__init__(adapter, message_adapter, message_queue_name, person_id)

    def get_persons_with_roles_in_organization(self, organization_id: str):
        """
        Fetch all people in the given organization along with their roles, email,
        phone number, invitation status, and a comprehensive list of all organizations
        they are part of, including their specific roles in each.
        """
        # Filter out 'employee' role
        filtered_roles = [role for role in self.VALID_ROLES if role != PersonOrganizationRoleEnum.EMPLOYEE.value]
        roles_regex_pattern = '|'.join([f'\\y{role}\\y' for role in filtered_roles])

        initial_persons_query = f"""
            SELECT DISTINCT ON (poi.email)
                poi.entity_id,
                poi.invitee_id AS person_id,
                poi.first_name,
                poi.last_name,
                poi.email,
                poi.status
            FROM person_organization_invitation AS poi
            WHERE poi.organization_id = %s
            AND poi.roles ~* %s
            ORDER BY poi.email, poi.changed_on DESC;
        """
        params1 = (organization_id, roles_regex_pattern)

        with self.adapter:
            initial_persons = self.adapter.execute_query(initial_persons_query, params1)

        if not initial_persons:
            return []

        person_emails = tuple([p['email'] for p in initial_persons])

        all_memberships_query = f"""
            SELECT
                p.email,
                o.name AS organization_name,
                p.roles
            FROM
                person_organization_invitation AS p
            JOIN
                "organization" AS o ON p.organization_id = o.entity_id
            WHERE
                p.email IN %s;
        """
        params2 = (person_emails,)

        with self.adapter:
            all_memberships_rows = self.adapter.execute_query(all_memberships_query, params2)

        # Group all memberships by email for easy lookup.
        memberships_by_email = defaultdict(list)
        if all_memberships_rows:
            for membership in all_memberships_rows:
                # Parse roles from the comma-separated string
                individual_roles = [role.strip() for role in (membership["roles"] or "").split(',') if role.strip()]
                
                memberships_by_email[membership['email']].append({
                    'organization_name': membership['organization_name'],
                    'roles': individual_roles
                })
                
        # Get phone numbers for all initial persons
        phone_numbers_by_person = {}
        person_ids = [p['person_id'] for p in initial_persons if p['person_id']]
        
        if person_ids:
            phone_query = """
                SELECT
                    pn.person_id,
                    pn.phone
                FROM
                    phone_number AS pn
                WHERE
                    pn.person_id IN %s;
            """
            params_phone = (tuple(person_ids),)

            with self.adapter:
                phone_rows = self.adapter.execute_query(phone_query, params_phone)

            for phone_row in phone_rows:
                phone_numbers_by_person[phone_row['person_id']] = phone_row['phone']

        # Assemble the final list.
        final_result = []
        for person in initial_persons:
            email = person['email']
            person_id = person['person_id']
            person_data = {
                "entity_id": person["entity_id"],
                "person_id": person_id,
                "first_name": person["first_name"],
                "last_name": person["last_name"],
                "email": email,
                "phone_number": phone_numbers_by_person.get(person_id) if person_id else None,
                "status": person["status"],
                # Assign the list of organizations grouped earlier
                "organizations": memberships_by_email.get(email, [])
            }
            final_result.append(person_data)

        return final_result

    def get_active_roles_for_person_in_organization(self, person_id: str, organization_id: str):
        placeholders = ", ".join(["%s"] * len(self.VALID_ROLES))
        q = f"""
            SELECT por.role
            FROM person_organization_role AS por
            WHERE por.person_id = %s
              AND por.organization_id = %s
              AND por.active = TRUE
              AND por.role IN ({placeholders})
            ORDER BY por.changed_on DESC;
        """
        with self.adapter:
            rows = self.adapter.execute_query(q, (person_id, organization_id, *self.VALID_ROLES))
        return [r["role"] for r in rows or []]

    def _select_role_entity_any_state(self, person_id: str, organization_id: str, role: str):
        q = """
            SELECT entity_id, active
            FROM person_organization_role
            WHERE person_id = %s AND organization_id = %s AND role = %s
            LIMIT 1;
        """
        with self.adapter:
            rows = self.adapter.execute_query(q, (person_id, organization_id, role))
        return rows[0] if rows else None  # {'entity_id': ..., 'active': t/f}

    def role_active(self, person_id: str, organization_id: str, role: str):
        """
        Ensure exactly ONE row exists for (person, org, role) and it's active.
        Returns: "reactivated" | "created" | "unchanged"
        """
        row = self._select_role_entity_any_state(person_id, organization_id, role)
        if row:
            if row["active"]:
                return "unchanged"
            # reactivate
            with self.adapter:
                self.adapter.execute_query(
                    "UPDATE person_organization_role SET active = TRUE WHERE entity_id = %s;",
                    (row["entity_id"],)
                )
            return "reactivated"

        # Use generic save to populate entity_id/version fields.
        new = PersonOrganizationRole(
            person_id=person_id,
            organization_id=organization_id,
            role=role,
            active=True
        )
        self.save(new)

        return "created"

    def role_inactive(self, person_id: str, organization_id: str, role: str) -> bool:
        """
        Ensure the row exists and is inactive. Returns True if changed state to inactive.
        """
        row = self._select_role_entity_any_state(person_id, organization_id, role)
        if not row:
            return False
        if row["active"]:
            with self.adapter:
                self.adapter.execute_query(
                    "UPDATE person_organization_role SET active = FALSE WHERE entity_id = %s;",
                    (row["entity_id"],)
                )
            return True
        return False
        
    def delete_roles_for_person_in_organization(self, person_id: str, organization_id: str):
        """
        Delete all roles for a person in an organization.
        
        Args:
            person_id (str): The ID of the person.
            organization_id (str): The ID of the organization.
            
        Returns:
            bool: True if deletion was successful.
        """
        query = """
            DELETE FROM person_organization_role
            WHERE person_id = %s AND organization_id = %s
        """
        params = (person_id, organization_id)
        
        with self.adapter:
            self.adapter.execute_query(query, params)
            
        return True

