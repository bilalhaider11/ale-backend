
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

    def upsert_employee(self, record: Employee, organization_id: str) -> dict:
        """
        Upsert a single employee record based on first_name, last_name, employee_id, and organization_id.
        Create Person if missing.
        """
        from common.services import PersonService
        from common.services import OrganizationService
        from common.app_config import config
        
        person_service = PersonService(config)
    
        if not record.organization_id:
            record.organization_id = organization_id
    
        key = (record.first_name, record.last_name, record.employee_id)
    
        # Find existing employee
        existing_employees = self.get_many({"organization_id": organization_id})
        existing_employees_map = {(emp.first_name, emp.last_name, emp.employee_id): emp for emp in existing_employees}
        
        if key in existing_employees_map:
            # Update existing
            
            existing_record = existing_employees_map[key]
            record.entity_id = existing_record.entity_id
            record.person_id = existing_record.person_id
            record.version = existing_record.version
            record.email_address = existing_record.email_address,
            record.previous_version = existing_record.previous_version
            
            self.save(record)
            
            return {"status": "updated", "employee_id": record.employee_id,"person_id":record.person_id}
        else:
            # Create new person and employee
            if record.email_address:
                existing_person = person_service.get_person_by_email_address(record.email_address)
                if existing_person:
                    record.person_id = existing_person.entity_id
                else:
                    new_person = Person(first_name=record.first_name, last_name=record.last_name)
                    record.person_id = new_person.entity_id
                    person_service.save_persons([new_person])
            else:
                new_person = Person(first_name=record.first_name, last_name=record.last_name)
                record.person_id = new_person.entity_id
                person_service.save_persons([new_person])
    
            self.save(record)
            return {"status": "inserted", "employee_id": record.employee_id, "person_id":record.person_id}


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
    
    def update_employee_id(self, employee_id, organization_id:str, entity_id: str,):
        
        query = """
        
        update employee set employee_id = %s where organization_id = %s and entity_id = %s
        
        """
        with self.adapter:
            result = self.adapter.execute_query(query, (employee_id, organization_id, entity_id))

        if result:
            return Employee(**result[0])

        return None