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
    
    def find_exclusion_matches(self, organization_id: str = None) -> List[EmployeeExclusionMatch]:
        """
        Finds matches between current employees/caregivers and OIG exclusion list.
        
        Args:
            organization_id: Optional organization ID to filter current employees
            
        Returns a list of EmployeeExclusionMatch objects for matched records.
        """
        # Build the base query
        query = """
            SELECT 
                ec.first_name,
                ec.last_name,
                oig.date_of_birth,
                oig.exclusion_type,
                oig.exclusion_date,
                ec.employee_id,
                oig.id AS oig_exclusion_id,
                ec.organization_id,
                CASE 
                    WHEN ec.date_of_birth = oig.date_of_birth THEN 'name_and_dob'
                    ELSE 'name_only'
                END AS match_type
            FROM current_employee ec
            INNER JOIN oig_employees_exclusion oig ON 
                LOWER(ec.first_name) = LOWER(oig.first_name) AND
                LOWER(ec.last_name) = LOWER(oig.last_name)
        """
        
        # Add organization filter if provided
        params = []
        if organization_id:
            query += " WHERE ec.organization_id = %s"
            params.append(organization_id)
        
        with self.adapter:
            results = self.adapter.execute_query(query, params if params else None)

        matches = []
        
        for row in results:
            match = EmployeeExclusionMatch(
                first_name=row['first_name'],
                last_name=row['last_name'],
                date_of_birth=row['date_of_birth'],
                exclusion_type=row['exclusion_type'],
                exclusion_date=row['exclusion_date'],
                employee_id=row['employee_id'],
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
                match.employee_id,
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
                record.employee_id,
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
