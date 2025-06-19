from common.repositories.base import BaseRepository
from common.models.oig_employees_exclusion import OigEmployeesExclusion

class OigEmployeesExclusionRepository(BaseRepository):
    MODEL = OigEmployeesExclusion

    def __init__(self, adapter, message_adapter, message_queue_name, person_id):
        super().__init__(adapter, message_adapter, message_queue_name, person_id)
    
    def truncate_table(self):
        """
        Truncate the oig_employees_exclusion table to remove all records.
        """
        query = "TRUNCATE TABLE oig_employees_exclusion"
        
        with self.adapter:
            self.adapter.execute_query(query)
        
        return True
        
    def insert_exclusion(self, record: OigEmployeesExclusion):
        """
        Insert a single OIG employee exclusion record into the database.
        
        Args:
            record: OigEmployeesExclusion instance to insert
        """
        # Build SQL insert statement
        columns = [k for k, v in record.__dict__.items() if v is not None and k != 'id']
        values = [getattr(record, col) for col in columns]
        placeholders = ', '.join(['%s'] * len(values))
        cols_str = ', '.join([f'"{col}"' for col in columns])
        
        query = f"""
            INSERT INTO oig_employees_exclusion ({cols_str})
            VALUES ({placeholders})
        """
        
        self.adapter.execute_query(query, values)

    def get_by_id(self, id) -> OigEmployeesExclusion:
        """
        Get an OIG employee exclusion record by its ID.
        """
        query = "SELECT * FROM oig_employees_exclusion WHERE id = %s"
        with self.adapter:
            result = self.adapter.execute_query(query, (id,))

        if result:
            return OigEmployeesExclusion(**result[0])
        
        return None
