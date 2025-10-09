revision = "0000000057"
down_revision = "0000000056"


def upgrade(migration):
    # Add patient_care_slot_id column to care_visit table
    migration.add_column(
        table_name="care_visit",
        column_name="patient_care_slot_id",
        datatype="VARCHAR(64) DEFAULT NULL"
    )
    
    # Add availability_slot_id column to care_visit table
    migration.add_column(
        table_name="care_visit",
        column_name="availability_slot_id",
        datatype="VARCHAR(64) DEFAULT NULL"
    )
    
    # Add same columns to care_visit_audit table
    migration.add_column(
        table_name="care_visit_audit",
        column_name="patient_care_slot_id",
        datatype="VARCHAR(64) DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="care_visit_audit",
        column_name="availability_slot_id",
        datatype="VARCHAR(64) DEFAULT NULL"
    )
    
    # Create indexes on the new foreign key columns
    migration.add_index("care_visit", "care_visit_patient_care_slot_id_ind", "patient_care_slot_id")
    migration.add_index("care_visit", "care_visit_availability_slot_id_ind", "availability_slot_id")

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Remove indexes
    migration.remove_index("care_visit", "care_visit_patient_care_slot_id_ind")
    migration.remove_index("care_visit", "care_visit_availability_slot_id_ind")
    
    # Drop columns from care_visit table
    migration.drop_column("care_visit", "patient_care_slot_id")
    migration.drop_column("care_visit", "availability_slot_id")
    
    # Drop columns from care_visit_audit table
    migration.drop_column("care_visit_audit", "patient_care_slot_id")
    migration.drop_column("care_visit_audit", "availability_slot_id")

    migration.update_version_table(version=down_revision)

