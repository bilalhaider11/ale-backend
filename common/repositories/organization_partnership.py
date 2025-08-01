from common.repositories.base import BaseRepository
from common.models import OrganizationPartnership, OrganizationPartnershipStatusEnum
from typing import List, Tuple, Optional


class OrganizationPartnershipRepository(BaseRepository):
    MODEL = OrganizationPartnership

    def _get_partnership_base_query(self, organization_id: str) -> Tuple[str, List[str]]:
        """
        Returns the shared SELECT + JOIN clause for organization partnerships, along with initial params.
        """
        if not organization_id:
            raise ValueError("organization_id is required.")

        base_query = f"""
            SELECT
                op.*,
                p1.first_name || ' ' || p1.last_name AS requested_by_name,
                p2.first_name || ' ' || p2.last_name AS responded_by_name,
                o.name AS organization_name
            FROM organization_partnership op
            LEFT JOIN person p1 ON op.requested_by_id = p1.entity_id
            LEFT JOIN person p2 ON op.responded_by_id = p2.entity_id
            LEFT JOIN organization o ON o.entity_id = CASE
                WHEN op.organization_1_id = %s THEN op.organization_2_id
                ELSE op.organization_1_id
            END
        """
        return base_query, [organization_id]


    def get_all_organization_partnerships(self, organization_id: str = None, status: OrganizationPartnershipStatusEnum = None) -> List[dict]:
        """
        Get all partnerships for a given organization, including requested_by name and the other organization's name.
        """
        base_query, params = self._get_partnership_base_query(organization_id)

        conditions = ['op.active', '(op.organization_1_id = %s OR op.organization_2_id = %s)']
        params.extend([organization_id, organization_id])

        if status:
            conditions.append('(op.status = %s)')
            params.append(status.value)

        where_clause = " AND ".join(conditions)

        full_query = f"""
            {base_query}
            WHERE {where_clause}
            ORDER BY op.created_at DESC;
        """

        with self.adapter:
            result = self.adapter.execute_query(full_query, params)

        return result if result else []


    def get_organization_partnership_by_id(self, organization_partnership_id: str, organization_id: str) -> Optional[dict]:
        """
        Get a specific organization partnership by its ID, enriched with requested_by name and the other organization's name.
        """
        base_query, params = self._get_partnership_base_query(organization_id)

        full_query = f"""
            {base_query}
            WHERE op.entity_id = %s AND op.active = true
            AND (op.organization_1_id = %s OR op.organization_2_id = %s)
            LIMIT 1;
        """

        # entity_id, org_id, org_id (for CASE and org filter)
        params.extend([organization_partnership_id, organization_id, organization_id])

        with self.adapter:
            result = self.adapter.execute_query(full_query, params)

        return result[0] if result else None

    def get_active_partner_ids_for_organization(self, organization_id: str) -> List[str]:
        """
        Get IDs of all active partnerships for a given organization.
        Args:
            organization_id: The ID of the organization
        Returns:
            List of organization IDs that are partners with the given organization
        """
        query = """
            SELECT 
                CASE 
                    WHEN organization_1_id = %s THEN organization_2_id 
                    ELSE organization_1_id 
                END AS partner_id
            FROM organization_partnership
            WHERE 
                active = true AND
                status = 'active' AND
                (organization_1_id = %s OR organization_2_id = %s)
        """
        params = [organization_id, organization_id, organization_id]
        with self.adapter:
            rows = self.adapter.execute_query(query, params)
        return [row['partner_id'] for row in rows]
