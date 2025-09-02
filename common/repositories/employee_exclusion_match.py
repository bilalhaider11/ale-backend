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


    def find_exclusion_matches_for_employee(self, employee_id: str) -> List[EmployeeExclusionMatch]:
        query = """
            SELECT 
                COALESCE(p.first_name, ec.first_name) AS first_name,
                COALESCE(p.last_name, ec.last_name) AS last_name,
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
            LEFT JOIN person p ON ec.person_id IS NOT NULL AND p.entity_id = ec.person_id
            JOIN oig_employees_exclusion oig ON 
                LOWER(COALESCE(p.first_name, ec.first_name)) = LOWER(oig.first_name) AND
                LOWER(COALESCE(p.last_name, ec.last_name)) = LOWER(oig.last_name)
            WHERE ec.entity_id = %s
        """
        params = (employee_id,)

        with self.adapter:
            results = self.adapter.execute_query(query, params)

        return [EmployeeExclusionMatch(**row) for row in results] if results else []


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
                COALESCE(p.first_name, ec.first_name) AS first_name,
                COALESCE(p.last_name, ec.last_name) AS last_name,
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
            LEFT JOIN person p ON ec.person_id IS NOT NULL AND p.entity_id = ec.person_id
            JOIN oig_employees_exclusion oig ON 
                LOWER(COALESCE(p.first_name, ec.first_name)) = LOWER(oig.first_name) AND
                LOWER(COALESCE(p.last_name, ec.last_name)) = LOWER(oig.last_name)
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


    def upsert_matches(self, records: List[EmployeeExclusionMatch], organization_id=None) -> List[EmployeeExclusionMatch]:
        """
        Upsert a list of employee exclusion match records using efficient targeted queries.
        Since there's no unique constraint for ON CONFLICT, we use a more efficient
        approach than loading all records into memory.
        
        Args:
            records: List of EmployeeExclusionMatch instances to upsert
            
        Returns:
            List[EmployeeExclusionMatch]: List of all processed EmployeeExclusionMatch records
        """
        if not records:
            return []
        
        logger.info(f"Upserting {len(records)} employee exclusion match records...")
        
        processed_records = []
        
        # Check if records exist using a single query to get all existing matches
        existing_matches = self._get_existing_matches_for_records(records, organization_id)
        
        # Process each record
        for record in records:
            # Set default values for new records
            if not record.status:
                record.status = 'pending'
            if record.reviewer_notes is None:
                record.reviewer_notes = None
            
            # Create the key to check against existing matches
            key = (
                record.first_name,
                record.last_name,
                record.exclusion_type,
                record.exclusion_date,
                record.matched_entity_type,
                record.matched_entity_id,
                record.organization_id
            )
            
            if key in existing_matches:
                # Record exists, update it while preserving system fields
                existing_data = existing_matches[key]
                
                # Create updated record preserving system fields
                updated_record = EmployeeExclusionMatch(
                    entity_id=existing_data['entity_id'],
                    version=existing_data['version'],
                    previous_version=existing_data['previous_version'],
                    active=existing_data['active'],
                    changed_by_id=existing_data['changed_by_id'],
                    changed_on=existing_data['changed_on'],
                    first_name=record.first_name,
                    last_name=record.last_name,
                    date_of_birth=record.date_of_birth,
                    exclusion_type=record.exclusion_type,
                    exclusion_date=record.exclusion_date,
                    matched_entity_type=record.matched_entity_type,
                    matched_entity_id=record.matched_entity_id,
                    oig_exclusion_id=record.oig_exclusion_id,
                    match_type=record.match_type,
                    status=existing_data['status'],  # Preserve existing status
                    reviewer_notes=existing_data['reviewer_notes'],  # Preserve existing notes
                    organization_id=record.organization_id
                )
                
                self.save(updated_record)
                processed_records.append(updated_record)
            else:
                # Record doesn't exist, insert new record
                self.save(record)
                processed_records.append(record)
        
        logger.info(f"Upsert completed: {len(processed_records)} records processed.")
        return processed_records
    
    def _get_existing_matches_for_records(self, records: List[EmployeeExclusionMatch], organization_id=None) -> dict:
        """
        Get existing matches for the given records using a single query.
        Returns a dictionary keyed by the business key fields.
        """
        if not records:
            return {}
        
        # Build a query to get all existing matches for the given records
        placeholders = []
        params = []
        
        for record in records:
            placeholders.append("(%s, %s, %s, %s, %s, %s, %s)")
            params.extend([
                record.first_name,
                record.last_name,
                record.exclusion_type,
                record.exclusion_date,
                record.matched_entity_type,
                record.matched_entity_id,
                record.organization_id
            ])
        
        existing_query = f"""
            SELECT entity_id, status, reviewer_notes, version, previous_version,
                   active, changed_by_id, changed_on,
                   first_name, last_name, exclusion_type, exclusion_date,
                   matched_entity_type, matched_entity_id, organization_id
            FROM employee_exclusion_match 
            WHERE (first_name, last_name, exclusion_type, exclusion_date, 
                   matched_entity_type, matched_entity_id, organization_id) 
                  IN ({','.join(placeholders)})
        """
        
        if organization_id:
            existing_query += " AND organization_id = %s"
            params.append(organization_id)
        
        with self.adapter:
            existing_results = self.adapter.execute_query(existing_query, params)
        
        # Convert results to a dictionary keyed by the business key
        existing_matches = {}
        if existing_results:
            for row in existing_results:
                key = (
                    row['first_name'],
                    row['last_name'],
                    row['exclusion_type'],
                    row['exclusion_date'],
                    row['matched_entity_type'],
                    row['matched_entity_id'],
                    row['organization_id']
                )
                existing_matches[key] = row
        
        return existing_matches
