from typing import List
from common.repositories.base import BaseRepository
from common.models import EmployeeExclusionMatch


class EmployeeExclusionMatchRepository(BaseRepository):
    MODEL = EmployeeExclusionMatch

    def update_matches(self, matches: List[EmployeeExclusionMatch]) -> None:
        """
        Truncates the table and inserts the provided matches.
        """
        # Truncate the table first
        with self.adapter:
            self.adapter.execute_query("DELETE FROM employee_exclusion_match")

        # Insert all the new matches
        for match in matches:
            self.save(match)

    def get_all(self) -> List[EmployeeExclusionMatch]:
        """
        Returns all records from the employee_exclusion_match table.
        """
        return super().get_many({})

    def find_exclusion_matches(self) -> List[EmployeeExclusionMatch]:
        """
        Finds matches between current employees/caregivers and OIG exclusion list.
        Returns a list of EmployeeExclusionMatch objects for matched records.
        """
        query = """
            SELECT DISTINCT 
                ec.first_name as first_name,
                ec.last_name as last_name,
                ec.date_of_birth as date_of_birth
            FROM (
                SELECT first_name, last_name, date_of_birth FROM current_employee
                UNION
                SELECT first_name, last_name, date_of_birth FROM current_caregiver
            ) AS ec
            INNER JOIN oig_employees_exclusion oig ON 
                LOWER(ec.first_name) = LOWER(oig.first_name) AND
                LOWER(ec.last_name) = LOWER(oig.last_name) AND
                ec.date_of_birth = oig.date_of_birth;
        """
        
        with self.adapter:
            results = self.adapter.execute_query(query)

        matches = []
        
        for row in results:
            match = EmployeeExclusionMatch(
                first_name=row['first_name'],
                last_name=row['last_name'],
                date_of_birth=row['date_of_birth']
            )
            matches.append(match)
            
        return matches
