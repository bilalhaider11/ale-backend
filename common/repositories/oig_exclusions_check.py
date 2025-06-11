from common.repositories.base import BaseRepository
from common.models import OigExclusionsCheck


class OigExclusionsCheckRepository(BaseRepository):
    MODEL = OigExclusionsCheck

    def __init__(self, adapter, message_adapter, message_queue_name, person_id):
        super().__init__(adapter, message_adapter, message_queue_name, person_id)

    def get_all_checks(self):
        """
        Fetch all OIG exclusion checks from the database.
        Results are ordered by changed_on DESC.
        """
        query = """
            SELECT *
            FROM oig_exclusions_check
            ORDER BY changed_on DESC;
        """

        with self.adapter:
            rows = self.adapter.execute_query(query)

        # Convert rows to model instances
        checks = []
        for row in rows:
            check = self.MODEL.from_dict(row)
            checks.append(check)

        return checks
    
    def get_checks_by_status(self, status):
        """
        Fetch all OIG exclusion checks with the specified status.
        Results are ordered by changed_on DESC.
        """
        query = """
            SELECT *
            FROM oig_exclusions_check
            WHERE status = %s
            ORDER BY changed_on DESC;
        """

        params = (status,)

        with self.adapter:
            rows = self.adapter.execute_query(query, params)

        # Convert rows to model instances
        checks = []
        for row in rows:
            check = self.MODEL.from_dict(row)
            checks.append(check)

        return checks
