revision = "0000000035"
down_revision = "0000000034"


def upgrade(migration):
    # Add availability_slot_key column to care_visit table
    migration.add_column(
        table_name="care_visit", 
        column_name="availability_slot_key", 
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    # Add patient_care_slot_key column to care_visit table
    migration.add_column(
        table_name="care_visit", 
        column_name="patient_care_slot_key", 
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    # Add availability_slot_key column to care_visit_audit table
    migration.add_column(
        table_name="care_visit_audit", 
        column_name="availability_slot_key", 
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    # Add patient_care_slot_key column to care_visit_audit table
    migration.add_column(
        table_name="care_visit_audit", 
        column_name="patient_care_slot_key", 
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    # Add index on availability_slot_key column for care_visit table
    migration.add_index("care_visit", "care_visit_availability_slot_key_ind", "availability_slot_key")
    
    # Add index on patient_care_slot_key column for care_visit table
    migration.add_index("care_visit", "care_visit_patient_care_slot_key_ind", "patient_care_slot_key")
    
    # Add index on availability_slot_key column for care_visit_audit table
    migration.add_index("care_visit_audit", "care_visit_audit_availability_slot_key_ind", "availability_slot_key")
    
    # Add index on patient_care_slot_key column for care_visit_audit table
    migration.add_index("care_visit_audit", "care_visit_audit_patient_care_slot_key_ind", "patient_care_slot_key")

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Remove indexes on new columns
    migration.remove_index("care_visit", "care_visit_availability_slot_key_ind")
    migration.remove_index("care_visit", "care_visit_patient_care_slot_key_ind")
    migration.remove_index("care_visit_audit", "care_visit_audit_availability_slot_key_ind")
    migration.remove_index("care_visit_audit", "care_visit_audit_patient_care_slot_key_ind")
    
    # Drop availability_slot_key column from care_visit table
    migration.drop_column("care_visit", "availability_slot_key")
    
    # Drop patient_care_slot_key column from care_visit table
    migration.drop_column("care_visit", "patient_care_slot_key")
    
    # Drop availability_slot_key column from care_visit_audit table
    migration.drop_column("care_visit_audit", "availability_slot_key")
    
    # Drop patient_care_slot_key column from care_visit_audit table
    migration.drop_column("care_visit_audit", "patient_care_slot_key")

    migration.update_version_table(version=down_revision)
