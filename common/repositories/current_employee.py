from common.repositories.base import BaseRepository
from common.models.current_employee import CurrentEmployee
from common.app_logger import logger

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

    def upsert_employees(self, records: list[CurrentEmployee], organization_id: str) -> dict:
        """
        Upsert a list of current employee records based on first_name, last_name, 
        employee_id, and organization_id attributes.
        
        Args:
            records: List of CurrentEmployee instances to upsert
            organization_id: The organization ID to filter existing records
            
        Returns:
            dict: Dictionary with 'inserted' and 'updated' counts
        """
        if not records:
            return {'inserted': 0, 'updated': 0}
        
        # Get all existing employees for this organization
        query = "SELECT * FROM current_employee WHERE organization_id = %s"
        
        with self.adapter:
            existing_results = self.adapter.execute_query(query, (organization_id,))
        
        # Convert existing results to a dictionary keyed by (first_name, last_name, employee_id)
        existing_employees = {}
        if existing_results:
            for row in existing_results:
                key = (row.get('first_name'), row.get('last_name'), row.get('employee_id'))
                existing_employees[key] = row
        
        records_to_insert = []
        records_to_update = []
        
        # Process each record to determine if it should be inserted or updated
        for record in records:
            # Set organization_id if not already set
            if not record.organization_id:
                record.organization_id = organization_id
                
            key = (record.first_name, record.last_name, record.employee_id)
            
            if key in existing_employees:
                # Record exists, prepare for update
                existing_record = existing_employees[key]
                existing_id = existing_record['id']
                
                # Build update data with non-None fields
                update_data = {}
                for field_name, field_value in record.__dict__.items():
                    if field_value is not None and field_name != 'id':
                        update_data[field_name] = field_value
                
                if update_data:
                    update_record = CurrentEmployee(**update_data)
                    records_to_update.append((existing_id, update_record))
            else:
                # Record doesn't exist, prepare for insert
                records_to_insert.append(record)
        

        logger.info("Preparing to insert %s new records and update %s existing records.", len(records_to_insert), len(records_to_update))

        inserted_count = 0
        updated_count = 0
        
        # Perform batch inserts in chunks
        if records_to_insert:
            for idx, insert_batch in enumerate(self._batch_employees(records_to_insert, batch_size=500)):
                logger.info("Inserting batch %s of size %s", idx + 1, len(insert_batch))
                inserted_count += self._batch_insert_employees(insert_batch)
        
        # Perform batch updates in chunks
        if records_to_update:
            for idx, update_batch in enumerate(self._batch_employees(records_to_update, batch_size=500)):
                logger.info("Updating batch %s of size %s", idx + 1, len(update_batch))
                updated_count += self._batch_update_employees(update_batch)
        
        logger.info("Upsert employees completed: %s records inserted, %s records updated.", inserted_count, updated_count)
        return {'inserted': inserted_count, 'updated': updated_count}

    def _batch_employees(self, records: list[CurrentEmployee], batch_size: int = 1000):
        """
        Split a list of employee records into batches of specified size.
        
        Args:
            records: List of CurrentEmployee instances to batch
            batch_size: Size of each batch (default: 1000)
            
        Yields:
            List[CurrentEmployee]: Batches of employee records
        """
        for i in range(0, len(records), batch_size):
            yield records[i:i + batch_size]

    def _batch_insert_employees(self, records: list[CurrentEmployee]) -> int:
        """
        Perform batch insert of employee records.
        
        Args:
            records: List of CurrentEmployee instances to insert
            
        Returns:
            int: Number of records inserted
        """
        if not records:
            return 0
        
        # Get all unique columns across all records
        all_columns = set()
        for record in records:
            columns = [k for k, v in record.__dict__.items() if v is not None and k != 'id']
            all_columns.update(columns)
        
        all_columns = list(all_columns)
        cols_str = ', '.join([f'"{col}"' for col in all_columns])
        
        # Build values for all records
        all_values = []
        for record in records:
            record_values = []
            for col in all_columns:
                value = getattr(record, col, None)
                record_values.append(value)
            all_values.extend(record_values)
        
        # Build placeholders for batch insert
        placeholders_per_record = ', '.join(['%s'] * len(all_columns))
        all_placeholders = ', '.join([f'({placeholders_per_record})' for _ in records])
        
        query = f"""
            INSERT INTO current_employee ({cols_str})
            VALUES {all_placeholders}
        """
        with self.adapter:
            self.adapter.execute_query(query, all_values)
        return len(records)

    def _batch_update_employees(self, update_records: list[tuple]) -> int:
        """
        Perform batch update of employee records.
        
        Args:
            update_records: List of tuples (record_id, update_record)
            
        Returns:
            int: Number of records updated
        """
        if not update_records:
            return 0
        
        updated_count = 0
        
        # Group updates by the same set of fields to optimize queries
        updates_by_fields = {}
        for record_id, update_record in update_records:
            update_data = update_record.as_dict()
            fields_key = tuple(sorted(update_data.keys()))
            if fields_key not in updates_by_fields:
                updates_by_fields[fields_key] = []
            updates_by_fields[fields_key].append((record_id, update_data))
        
        # Execute batch updates for each group of fields
        for fields, records_group in updates_by_fields.items():
            if not fields:
                continue
                
            # Build the update query for this group
            set_clauses = [f'"{field}" = %s' for field in fields]
            set_str = ', '.join(set_clauses)
            
            # Build batch update with CASE statements
            case_statements = []
            all_values = []
            record_ids = []
            
            for field in fields:
                case_parts = []
                for record_id, update_data in records_group:
                    case_parts.append(f"WHEN id = %s THEN %s")
                    all_values.extend([record_id, update_data[field]])
                
                case_statement = f'"{field}" = CASE {" ".join(case_parts)} ELSE "{field}" END'
                case_statements.append(case_statement)
                
            # Collect all record IDs for the WHERE clause
            record_ids = [str(record_id) for record_id, _ in records_group]
            ids_placeholder = ', '.join(['%s'] * len(record_ids))
            
            update_query = f"""
                UPDATE current_employee 
                SET {', '.join(case_statements)}
                WHERE id IN ({ids_placeholder})
            """
            
            all_values.extend(record_ids)
            with self.adapter:
                self.adapter.execute_query(update_query, all_values)
            updated_count += len(records_group)
        
        return updated_count
