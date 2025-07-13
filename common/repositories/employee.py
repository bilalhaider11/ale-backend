import uuid

from common.repositories.base import BaseRepository
from common.models.employee import Employee
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

        # Build SQL insert statement
        columns = [k for k, v in record.__dict__.items() if v is not None and k != 'id']

        # Skip insertion if all fields are None
        if not columns:
            return

        values = [getattr(record, col) for col in columns]
        placeholders = ', '.join(['%s'] * len(values))
        cols_str = ', '.join([f'"{col}"' for col in columns])

        query = f"""
            INSERT INTO employee ({cols_str})
            VALUES ({placeholders})
        """

        self.adapter.execute_query(query, values)

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
                records_to_insert.append(record)


        logger.info("Preparing to insert %s new records and update %s existing records.", len(records_to_insert), len(records_to_update))

        inserted_count = 0
        updated_count = 0

        # Perform batch inserts in chunks
        if records_to_insert:
            for idx, insert_batch in enumerate(self._batch_employees(records_to_insert, batch_size=100)):
                logger.info("Inserting batch %s of size %s", idx + 1, len(insert_batch))
                inserted_count += self._batch_save_employees(insert_batch)

        # Perform batch updates in chunks
        if records_to_update:
            for idx, update_batch in enumerate(self._batch_employees(records_to_update, batch_size=100)):
                logger.info("Updating batch %s of size %s", idx + 1, len(update_batch))
                updated_count += self._batch_save_employees(update_batch)

        logger.info("Upsert employees completed: %s records inserted, %s records updated.", inserted_count, updated_count)
        return records_to_insert + records_to_update

    def _batch_employees(self, records: list[Employee], batch_size: int = 1000):
        """
        Split a list of employee records into batches of specified size.

        Args:
            records: List of Employee instances to batch
            batch_size: Size of each batch (default: 1000)

        Yields:
            List[Employee]: Batches of employee records
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
        Get all employees with their exclusion match counts.

        Args:
            organization_id: The organization ID to filter by

        Returns:
            List[Employee]: List of Employee instances with match details
        """
        query = """
            SELECT e.*,
                   CASE 
                       WHEN COUNT(CASE WHEN eem.match_type = 'name_and_dob' THEN 1 END) > 0 
                       THEN 'name_and_dob'
                       ELSE 'name_only'
                   END as match_type,
                   COUNT(eem.entity_id) as match_count
            FROM employee e
            INNER JOIN employee_exclusion_match eem ON e.entity_id = eem.employee_id
            WHERE e.organization_id = %s
            GROUP BY e.entity_id
        """

        with self.adapter:
            result = self.adapter.execute_query(query, (organization_id,))

        if result:
            employees = []
            for row in result:
                # Extract match_type and match_count from the row
                match_type = row.pop('match_type')
                match_count = row.pop('match_count')

                # Create Employee instance
                employee = Employee(**row)

                # Add match_type and match_count as attributes
                employee = employee.as_dict()
                employee['match_type'] = match_type
                employee['match_count'] = match_count

                employees.append(employee)

            return employees

        return []
