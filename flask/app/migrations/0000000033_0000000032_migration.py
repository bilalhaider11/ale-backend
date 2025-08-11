revision = "0000000033"
down_revision = "0000000032"


def upgrade(migration):
    # Add logical_key column to availability_slot table
    migration.add_column(
        table_name="availability_slot", 
        column_name="logical_key", 
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    # Add logical_key column to availability_slot_audit table
    migration.add_column(
        table_name="availability_slot_audit", 
        column_name="logical_key", 
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    # Populate logical_key column in availability_slot table
    migration.execute("""
        UPDATE availability_slot 
        SET logical_key = 
            employee_id || '-' || 
            day_of_week::TEXT || '-' || 
            TO_CHAR(start_time, 'HH24:MI:SS') || '-' || 
            TO_CHAR(end_time, 'HH24:MI:SS')
        WHERE employee_id IS NOT NULL 
        AND day_of_week IS NOT NULL 
        AND start_time IS NOT NULL 
        AND end_time IS NOT NULL;
    """)
    
    # Populate logical_key column in availability_slot_audit table
    migration.execute("""
        UPDATE availability_slot_audit 
        SET logical_key = 
            employee_id || '-' || 
            day_of_week::TEXT || '-' || 
            TO_CHAR(start_time, 'HH24:MI:SS') || '-' || 
            TO_CHAR(end_time, 'HH24:MI:SS')
        WHERE employee_id IS NOT NULL 
        AND day_of_week IS NOT NULL 
        AND start_time IS NOT NULL 
        AND end_time IS NOT NULL;
    """)
    
    # Add index on logical_key column for availability_slot table
    migration.add_index("availability_slot", "availability_slot_logical_key_ind", "logical_key")
    
    migration.update_version_table(version=revision)


def downgrade(migration):

    # Drop logical_key column from availability_slot table
    migration.drop_column("availability_slot", "logical_key")
    
    # Drop logical_key column from availability_slot_audit table
    migration.drop_column("availability_slot_audit", "logical_key")

    migration.update_version_table(version=down_revision)
