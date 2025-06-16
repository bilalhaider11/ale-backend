from common.repositories.base import BaseRepository
from common.models.current_caregiver import CurrentCaregiver

class CurrentCaregiverRepository(BaseRepository):
    MODEL = CurrentCaregiver

    def __init__(self, adapter, message_adapter, message_queue_name, person_id):
        super().__init__(adapter, message_adapter, message_queue_name, person_id)
    
    def truncate_table(self):
        """
        Truncate the current_caregiver table to remove all records.
        """
        query = "TRUNCATE TABLE current_caregiver"
        
        with self.adapter:
            self.adapter.execute_query(query)
        
        return True
        
    def insert_caregiver(self, record: CurrentCaregiver):
        """
        Insert a single current caregiver record into the database.
        
        Args:
            record: CurrentCaregiver instance to insert
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
            INSERT INTO current_caregiver ({cols_str})
            VALUES ({placeholders})
        """
        
        self.adapter.execute_query(query, values)
