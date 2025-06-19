from common.repositories.base import BaseRepository
from common.models.current_employee import CurrentEmployee

class CurrentEmployeeRepository(BaseRepository):
    MODEL = CurrentEmployee

    def __init__(self, adapter, message_adapter, message_queue_name, person_id):
        super().__init__(adapter, message_adapter, message_queue_name, person_id)
    
    def truncate_table(self):
        """
        Truncate the current_employee table to remove all records.
        """
        query = "TRUNCATE TABLE current_employee"
        
        with self.adapter:
            self.adapter.execute_query(query)
        
        return True 
        
    def insert_employee(self, record: CurrentEmployee):
        """
        Insert a single current employee record into the database.
        
        Args:
            record: CurrentEmployee instance to insert
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
            INSERT INTO current_employee ({cols_str})
            VALUES ({placeholders})
        """
        
        self.adapter.execute_query(query, values)

    def get_by_employee_id(self, employee_id: str) -> CurrentEmployee:
        """
        Get a current employee record by employee_id.
        
        Args:
            employee_id: The employee ID to search for
        
        Returns:
            CurrentEmployee instance if found, otherwise None
        """
        query = "SELECT * FROM current_employee WHERE employee_id = %s"
        
        with self.adapter:
            result = self.adapter.execute_query(query, (employee_id,))
        
        if result:
            return CurrentEmployee(**result[0])
        
        return None


    def get_employees_count(self) -> int:
        """
        Get the count of current employees in the database.
        Returns:
            int: The number of current employees
        """
        query = "SELECT COUNT(*) FROM current_employee;"
        
        with self.adapter:
            result = self.adapter.execute_query(query)
        
        if result:
            return result[0]['count']
        
        return None
