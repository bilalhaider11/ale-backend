from typing import List
from common.repositories.base import BaseRepository
from common.models import EmployeeExclusionMatch
from common.app_logger import logger


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

    def get_all(self, organization_id=None) -> List[EmployeeExclusionMatch]:
        """
        Returns all records from the employee_exclusion_match table.
        """
        conditions = {}
        if organization_id:
            conditions['organization_id'] = organization_id
        return super().get_many(conditions)
    
    def get_all_count(self, organization_id=None) -> int:
        """
        Get the count of employee exclusion matches in the database.
        Returns:
            int: The number of employee exclusion matches
        """
        query = "SELECT COUNT(*) FROM employee_exclusion_match;"

        if organization_id:
            query = "SELECT COUNT(*) FROM employee_exclusion_match WHERE organization_id = %s;"
            params = (organization_id,)
        else:
            params = None
        
        with self.adapter:
            result = self.adapter.execute_query(query, params if params else None)
        
        if result:
            return result[0]['count']
        
        return None


    def find_exclusion_matches(self, organization_id: str = None) -> List[EmployeeExclusionMatch]:
        """
        Finds matches between employees/caregivers/physicians and OIG exclusion list.
        
        Args:
            organization_id: Optional organization ID to filter entities
            
        Returns a list of EmployeeExclusionMatch objects for matched records from both employees and physicians.
        """
        matches = []
        
        # PART 1: Find employee matches by name
        # Build the base query for employees
        employee_query = """
            SELECT 
                ec.first_name,
                ec.last_name,
                oig.date_of_birth,
                oig.exclusion_type,
                oig.exclusion_date,
                'employee' AS matched_entity_type,
                ec.entity_id AS matched_entity_id,
                oig.id AS oig_exclusion_id,
                ec.organization_id,
                CASE 
                    WHEN ec.date_of_birth = oig.date_of_birth THEN 'name_and_dob'
                    ELSE 'name_only'
                END AS match_type
            FROM employee ec
            INNER JOIN oig_employees_exclusion oig ON 
                LOWER(ec.first_name) = LOWER(oig.first_name) AND
                LOWER(ec.last_name) = LOWER(oig.last_name)
        """
        
        # Add organization filter if provided
        employee_params = []
        if organization_id:
            employee_query += " WHERE ec.organization_id = %s"
            employee_params.append(organization_id)
        
        with self.adapter:
            employee_results = self.adapter.execute_query(employee_query, employee_params if employee_params else None)

        # Process employee matches
        for row in employee_results:
            match = EmployeeExclusionMatch(
                first_name=row['first_name'],
                last_name=row['last_name'],
                date_of_birth=row['date_of_birth'],
                exclusion_type=row['exclusion_type'],
                exclusion_date=row['exclusion_date'],
                matched_entity_type=row['matched_entity_type'],
                matched_entity_id=row['matched_entity_id'],
                oig_exclusion_id=row['oig_exclusion_id'],
                match_type=row['match_type'],
                status='pending',
                reviewer_notes=None,
                organization_id=row.get('organization_id', None),
            )
            matches.append(match)
            
        # PART 2: Find physician matches
        # Build the base query for physicians
        physician_query = """
            SELECT
                per.first_name,
                per.last_name,
                p.date_of_birth,
                oig.exclusion_type,
                oig.exclusion_date,
                'physician' AS matched_entity_type,
                p.entity_id     AS matched_entity_id,
                oig.id          AS oig_exclusion_id,
                p.organization_id,
                CASE
                    WHEN p.date_of_birth IS NOT NULL
                        AND p.date_of_birth::date = oig.date_of_birth
                    THEN 'name_and_dob'
                    ELSE 'name_only'
                END AS match_type
            FROM
                physician p
            INNER JOIN
                person per     ON p.person_id = per.entity_id
            INNER JOIN
                oig_employees_exclusion oig
                    ON  LOWER(per.first_name) = LOWER(oig.first_name)
                    AND LOWER(per.last_name)  = LOWER(oig.last_name)
        """
        # Add organization filter if provided
        physician_params = []
        if organization_id:
            physician_query += " WHERE p.organization_id = %s"
            physician_params.append(organization_id)
        
        with self.adapter:
            physician_results = self.adapter.execute_query(physician_query, physician_params if physician_params else None)

        # Process physician matches
        for row in physician_results:
            match = EmployeeExclusionMatch(
                first_name=row['first_name'],
                last_name=row['last_name'],
                date_of_birth=row['date_of_birth'],
                exclusion_type=row['exclusion_type'],
                exclusion_date=row['exclusion_date'],
                matched_entity_type=row['matched_entity_type'],
                matched_entity_id=row['matched_entity_id'],
                oig_exclusion_id=row['oig_exclusion_id'],
                match_type=row['match_type'],
                status='pending',
                reviewer_notes=None,
                organization_id=row.get('organization_id', None),
            )
            matches.append(match)
            
        return matches


    def upsert_matches(self, records: List[EmployeeExclusionMatch], organization_id=None) -> dict:
        """
        Upsert a list of employee exclusion match records based on first_name, last_name, 
        date_of_birth, exclusion_type, exclusion_date, employee_id, and organization_id attributes.
        
        Args:
            records: List of EmployeeExclusionMatch instances to upsert
            
        Returns:
            dict: Dictionary with 'inserted' and 'updated' counts
        """
        if not records:
            return {'inserted': 0, 'updated': 0}
        
        logger.info(f"Upserting {len(records)} employee exclusion match records...")

        # Get all existing employee exclusion matches
        existing_matches = self.get_all(organization_id=organization_id)

        # Convert existing results to a dictionary keyed by the match attributes
        existing_matches_dict = {}
        for match in existing_matches:
            key = (
                match.first_name,
                match.last_name,
                match.exclusion_type,
                match.exclusion_date,
                match.matched_entity_type,
                match.matched_entity_id,
                match.organization_id
            )
            existing_matches_dict[key] = match
        
        inserted_count = 0
        updated_count = 0
        
        # Process each record to determine if it should be inserted or updated
        logger.info(f"Saving {len(records)} employee exclusion match records...")
        for record in records:
            key = (
                record.first_name,
                record.last_name,
                record.exclusion_type,
                record.exclusion_date,
                record.matched_entity_type,
                record.matched_entity_id,
                record.organization_id
            )
            
            if key in existing_matches_dict:
                # Record exists, update it (excluding status and reviewer_notes)
                existing_match = existing_matches_dict[key]
                
                # Update fields except status and reviewer_notes
                for field_name, field_value in record.__dict__.items():
                    if (field_value is not None and 
                        field_name not in ['entity_id', 'version', 'previous_version', 
                                         'active', 'changed_by_id', 'changed_on',
                                         'status', 'reviewer_notes']):
                        setattr(existing_match, field_name, field_value)
                
                self.save(existing_match)
                updated_count += 1
            else:
                # Record doesn't exist, insert new record with default values
                if not record.status:
                    record.status = 'pending'
                if record.reviewer_notes is None:
                    record.reviewer_notes = None
                
                self.save(record)
                inserted_count += 1
        
        logger.info(f"Upsert completed: {inserted_count} inserted, {updated_count} updated.")
        return {'inserted': inserted_count, 'updated': updated_count}
