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
