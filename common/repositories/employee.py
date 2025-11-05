import uuid

from common.repositories.base import BaseRepository
from common.models import Employee, Person
from rococo.models import VersionedModel
from common.app_logger import logger


class EmployeeRepository(BaseRepository):
    MODEL = Employee

    def __init__(self, adapter, message_adapter, message_queue_name, person_id):
        super().__init__(adapter, message_adapter, message_queue_name, person_id)
        
    def insert_employee(self, record: Employee):
        """
        Insert a single employee record into the database.

        Args:
            record: Employee instance to insert
        """

        return self.save(record)

    def get_by_employee_id(self, employee_id: str, organization_id: str) -> Employee:
        """
        Get an employee record by employee_id.

        Args:
            employee_id: The employee ID to search for
            organization_id: The organization ID to filter by
        Returns:
            Employee instance if found, otherwise None
        """
        query = "SELECT * FROM employee WHERE employee_id = %s AND organization_id = %s"

        with self.adapter:
            result = self.adapter.execute_query(query, (employee_id, organization_id))

        if result:
            return Employee(**result[0])

        return None
    
    def get_employee_ids_map_for_organization(self, organization_id: str) -> dict:
        """
        Get a dictionary mapping employee_id to Employee objects for an organization.
        Used for efficient duplicate checking during bulk imports.

        Args:
            organization_id: The organization ID to filter by
        Returns:
            dict: {employee_id: Employee} mapping
        """
        query = "SELECT * FROM employee WHERE organization_id = %s AND active = true"

        with self.adapter:
            result = self.adapter.execute_query(query, (organization_id,))

        if result:
            return {row['employee_id']: Employee(**row) for row in result if row.get('employee_id')}

        return {}
   
#####################################################################################
    
    def get_all_employee_ids(self,organization_id=None) -> list:
        
        query = "SELECT employee_id FROM employee"
        
        with self.adapter:
            result = self.adapter.execute_query(query if query else None)
            
        if result:
            return result
        
        return result
        
        


    def get_employees_count(self, organization_id=None) -> int:
        """
        Get the count of employees in the database.
        Returns:
            int: The number of employees
        """
        query = "SELECT COUNT(*) FROM employee;"

        if organization_id:
            query = "SELECT COUNT(*) FROM employee WHERE organization_id = %s;"
            params = (organization_id,)
        else:
            params = None

        with self.adapter:
            result = self.adapter.execute_query(query, params if params else None)

        if result:
            return result[0]['count']

        return None

    def upsert_employees(self, records: list[Employee], organization_id: str) -> dict:
        """
        Upsert a list of employee records based on first_name, last_name,
        employee_id, and organization_id attributes.

        Args:
            records: List of Employee instances to upsert
            organization_id: The organization ID to filter existing records

        Returns:
            dict: Dictionary with 'inserted' and 'updated' counts
        """
        if not records:
            return {'inserted': 0, 'updated': 0}


        existing_employees = self.get_many({"organization_id": organization_id})

        # Convert existing results to a dictionary keyed by (first_name, last_name, employee_id)
        existing_employees_map = {}
        if existing_employees:
            for employee in existing_employees:
                key = (employee.first_name, employee.last_name, employee.employee_id)
                existing_employees_map[key] = employee

        records_to_insert = []
        records_to_update = []

        from common.services import PersonService
        from common.app_config import config
        person_service = PersonService(config)

        person_records_to_insert = []

        # Process each record to determine if it should be inserted or updated
        for record in records:
            # Set organization_id if not already set
            if not record.organization_id:
                record.organization_id = organization_id

            key = (record.first_name, record.last_name, record.employee_id)

            if key in existing_employees_map:
                # Record exists, prepare for update
                existing_record = existing_employees_map[key]
                existing_id = existing_record.entity_id
                existing_person_id = existing_record.person_id

                record.entity_id = existing_id  # Ensure the record has the existing ID for update
                record.version = existing_record.version  # Use the existing version for update
                record.previous_version = existing_record.previous_version
                record.person_id = existing_person_id  # Retain the existing person_id

                records_to_update.append(record)
            else:
                # Record doesn't exist, prepare for insert

                def names_differ(person1, person2):
                    return (
                        person1.first_name.strip().lower() != person2.first_name.strip().lower() or
                        person1.last_name.strip().lower() != person2.last_name.strip().lower()
                    )

                def create_and_attach_person(record):
                    person = Person(first_name=record.first_name, last_name=record.last_name)
                    record.person_id = person.entity_id
                    person_records_to_insert.append(person)
                    return person

                # Check if the person needs to be merged.
                if record.email_address:
                    existing_person = person_service.get_person_by_email_address(record.email_address)

                    if existing_person:
                        if names_differ(existing_person, record):
                            # Email exists but name is different — create and attach new person
                            create_and_attach_person(record)
                        else:
                            # Match found — use existing person
                            record.person_id = existing_person.entity_id
                    else:
                        # Email not found — create new person
                        create_and_attach_person(record)
                else:
                    # No email — create new person
                    create_and_attach_person(record)
                
                records_to_insert.append(record)


        logger.info("Preparing to insert %s new records and update %s existing records.", len(records_to_insert), len(records_to_update))

        inserted_count = 0
        updated_count = 0

        # Perform batch inserts in chunks
        if records_to_insert:
            for idx, insert_batch in enumerate(self._batch_records(records_to_insert, batch_size=100)):
                logger.info("Inserting batch %s of size %s", idx + 1, len(insert_batch))
                inserted_count += self._batch_save_employees(insert_batch)

        # Perform batch updates in chunks
        if records_to_update:
            for idx, update_batch in enumerate(self._batch_records(records_to_update, batch_size=100)):
                logger.info("Updating batch %s of size %s", idx + 1, len(update_batch))
                updated_count += self._batch_save_employees(update_batch)

        # Save person records if any
        if person_records_to_insert:
            for idx, person_batch in enumerate(self._batch_records(person_records_to_insert, batch_size=100)):
                logger.info("Inserting person batch %s of size %s", idx + 1, len(person_batch))
                person_service.save_persons(person_batch)

        logger.info("Upsert employees completed: %s records inserted, %s records updated.", inserted_count, updated_count)
        logger.info("%s person records inserted.", len(person_records_to_insert))
        return records_to_insert + records_to_update

    def _batch_records(self, records: list[VersionedModel], batch_size: int = 1000):
        """
        Split a list of versioned model records into batches of specified size.

        Args:
            records: List of VersionedModel instances to batch
            batch_size: Size of each batch (default: 1000)

        Yields:
            List[VersionedModel]: Batches of VersionedModel records
        """
        for i in range(0, len(records), batch_size):
            yield records[i:i + batch_size]

    def _batch_save_employees(self, records: list[Employee]) -> int:
        """
        Save a batch of employee records to the database.
        Args:
            records: List of Employee instances to save
        Returns:
            int: Number of records saved
        """
        if not records:
            return 0
        for record in records:
            record = self.save(record)
        return len(records)


    def get_employees_with_matches(self, organization_id: str):
        """
        Get all employees and physicians with their exclusion match counts.

        Args:
            organization_id: The organization ID to filter by

        Returns:
            List[dict]: List of entity dictionaries with match details
                    Each dictionary has an 'entity_type' field that is either 'employee' or 'physician'
        """
        # First, get the employee matches
        employee_query = """
            SELECT e.*,
                   CASE 
                       WHEN COUNT(CASE WHEN eem.match_type = 'name_and_dob' THEN 1 END) > 0 
                       THEN 'name_and_dob'
                       ELSE 'name_only'
                   END as match_type,
                   COUNT(eem.entity_id) as match_count,
                   CASE 
                       WHEN COUNT(CASE WHEN eem.status = 'pending' THEN 1 END) > 0 
                       THEN 'pending'
                       ELSE 'handled'
                   END as status,
                   MAX(eem.verification_result) as verification_result,
                   MAX(eem.s3_key) as s3_key
            FROM employee e
                INNER JOIN employee_exclusion_match eem ON e.entity_id = eem.matched_entity_id
                WHERE e.organization_id = %s AND eem.matched_entity_type = 'employee'
                GROUP BY e.entity_id
        """

        with self.adapter:
            employee_results = self.adapter.execute_query(employee_query, (organization_id,))

        # Now, get the physician matches - we'll use a direct SQL query
        physician_query = """
            SELECT p.*,
                per.first_name,
                per.last_name,
                CASE
                    WHEN COUNT(CASE WHEN eem.match_type = 'name_and_dob' THEN 1 END) > 0
                    THEN 'name_and_dob'
                    ELSE 'name_only'
                END AS match_type,
                COUNT(eem.entity_id) AS match_count,
                CASE
                    WHEN COUNT(CASE WHEN eem.status = 'pending' THEN 1 END) > 0
                    THEN 'pending'
                    ELSE 'handled'
                END AS status,
                MAX(eem.verification_result) as verification_result,
                MAX(eem.s3_key) as s3_key
            FROM physician p
            INNER JOIN person per ON p.person_id = per.entity_id
            INNER JOIN employee_exclusion_match eem ON p.entity_id = eem.matched_entity_id
            WHERE p.organization_id = %s
            AND eem.matched_entity_type = 'physician'
            GROUP BY p.entity_id, per.first_name, per.last_name
        """

        with self.adapter:
            physician_results = self.adapter.execute_query(physician_query, (organization_id,))

        results = []

        # Process employee results
        if employee_results:
            for row in employee_results:
                # Extract match_type, match_count, verification_result, and s3_key from the row
                match_type = row.pop('match_type')
                match_count = row.pop('match_count')
                match_status = row.pop('status')
                verification_result = row.pop('verification_result')
                s3_key = row.pop('s3_key')

                # Create Employee instance
                employee = Employee(**row)

                # Add match_type, match_count, verification_result, and s3_key as attributes
                employee_dict = employee.as_dict()
                employee_dict['match_type'] = match_type
                employee_dict['match_count'] = match_count
                employee_dict['status'] = match_status
                employee_dict['verification_result'] = verification_result
                employee_dict['s3_key'] = s3_key
                employee_dict['entity_type'] = 'employee'

                results.append(employee_dict)

        # Process physician results
        if physician_results:
            for row in physician_results:
                # Extract match_type, match_count, verification_result, s3_key, and names from the row
                match_type = row.pop('match_type')
                match_count = row.pop('match_count')
                match_status = row.pop('status')
                verification_result = row.pop('verification_result')
                s3_key = row.pop('s3_key')
                first_name = row.pop('first_name', None)
                last_name = row.pop('last_name', None)

                # Create a dictionary from the row
                physician_dict = dict(row)
                physician_dict['match_type'] = match_type
                physician_dict['match_count'] = match_count
                physician_dict['status'] = match_status
                physician_dict['verification_result'] = verification_result
                physician_dict['s3_key'] = s3_key
                physician_dict['entity_type'] = 'physician'
                
                # Add names from person record if available
                if first_name:
                    physician_dict['first_name'] = first_name
                if last_name:
                    physician_dict['last_name'] = last_name

                results.append(physician_dict)

        return results


    def get_employees_with_invitation_status(self, organization_ids: list[str], employee_type: str = None):
        """
        Get all employees with their invitation status.

        Args:
            organization_ids: The organization IDs to filter by
            employee_type: Optional employee type to filter by

        Returns:
            List[Employee]: List of Employee instances with invitation status
        """
        query = """
            SELECT e.*,
                   o.name as organization_name,
                   CASE
                       WHEN pir.status = 'active' THEN 'active'
                       WHEN pir.status = 'pending' THEN 'pending'
                       ELSE NULL
                   END as invitation_status
            FROM employee e
                LEFT JOIN person_organization_invitation pir ON e.person_id = pir.invitee_id AND pir.organization_id = e.organization_id
                LEFT JOIN organization o ON e.organization_id = o.entity_id
                WHERE e.organization_id IN %s
        """
        
        params = [tuple(organization_ids)]
        
        if employee_type:
            query += " AND e.employee_type = %s"
            params.append(employee_type)

        with self.adapter:
            result = self.adapter.execute_query(query, tuple(params))

        if result:
            employees = []
            for row in result:
                # Extract invitation_status and organization_name from the row
                invitation_status = row.pop('invitation_status')
                organization_name = row.pop('organization_name')

                # Create Employee instance
                employee = Employee(**row)

                # Add invitation_status and organization_name as attributes
                employee = employee.as_dict()
                employee['invitation_status'] = invitation_status
                employee['organization_name'] = organization_name

                employees.append(employee)

            return employees

        return []