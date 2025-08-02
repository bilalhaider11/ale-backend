from common.repositories.base import BaseRepository
from common.models.organization import Organization


class OrganizationRepository(BaseRepository):
    MODEL = Organization

    def get_organizations_by_person_id(self, person_id: str):
        query = """
            SELECT o.*, por.role
            FROM organization AS o
            JOIN person_organization_role AS por
            ON o.entity_id = por.organization_id
            WHERE por.person_id = %s;
        """
        params = (person_id,)

        with self.adapter:
            results = self.adapter.execute_query(query, params)
            return results

    def get_partner_organizations(self, organization_id: str):
        query = """
            SELECT o.*
                FROM organization_partnership op
                JOIN organization o ON o.entity_id = 
                    CASE 
                        WHEN op.organization_1_id = %s THEN op.organization_2_id
                        ELSE op.organization_1_id
                    END
                WHERE 
                    op.active = true
                    AND op.status = 'active'
                    AND (%s = op.organization_1_id OR %s = op.organization_2_id)
        """
        params = (organization_id, organization_id, organization_id)

        with self.adapter:
            results = self.adapter.execute_query(query, params)
        return results if results else []
