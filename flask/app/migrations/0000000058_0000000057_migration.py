revision = "0000000058"
down_revision = "0000000057"

def upgrade(migration):
    # Add availability_slot_key column to care_visit table
    migration.add_column(
        table_name="care_visit", 
        column_name="availability_slot_id", 
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    # Add patient_care_slot_key column to care_visit table
    migration.add_column(
        table_name="care_visit", 
        column_name="patient_care_slot_id", 
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="care_visit_audit", 
        column_name="availability_slot_id", 
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    # Add patient_care_slot_key column to care_visit_audit table
    migration.add_column(
        table_name="care_visit_audit", 
        column_name="patient_care_slot_id", 
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    migration.update_version_table(version=revision)

def downgrade(migration):
    
    # Drop availability_slot_key column from care_visit table
    migration.drop_column("care_visit", "availability_slot_id")
    
    # Drop patient_care_slot_key column from care_visit table
    migration.drop_column("care_visit", "patient_care_slot_id")
    
       # Drop availability_slot_key column from care_visit_audit table
    migration.drop_column("care_visit_audit", "availability_slot_id")
    
    # Drop patient_care_slot_key column from care_visit_audit table
    migration.drop_column("care_visit_audit", "patient_care_slot_id")
    
    migration.update_version_table(version=down_revision)
