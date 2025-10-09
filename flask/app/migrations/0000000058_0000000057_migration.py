revision = "0000000058"
down_revision = "0000000057"


def upgrade(migration):
    # Drop old logical_key columns from patient_care_slot table
    migration.drop_column("patient_care_slot", "logical_key")
    
    # Drop old logical_key columns from patient_care_slot_audit table
    migration.drop_column("patient_care_slot_audit", "logical_key")
    
    # Drop old logical_key columns from availability_slot table
    migration.drop_column("availability_slot", "logical_key")
    
    # Drop old logical_key columns from availability_slot_audit table
    migration.drop_column("availability_slot_audit", "logical_key")
    
    # Drop old key columns from care_visit table
    migration.drop_column("care_visit", "patient_care_slot_key")
    migration.drop_column("care_visit", "availability_slot_key")
    
    # Drop old key columns from care_visit_audit table
    migration.drop_column("care_visit_audit", "patient_care_slot_key")
    migration.drop_column("care_visit_audit", "availability_slot_key")
    
    # Drop redundant patient_id and employee_id columns from care_visit
    migration.drop_column("care_visit", "patient_id")
    migration.drop_column("care_visit", "employee_id")
    
    # Drop redundant patient_id and employee_id columns from care_visit_audit
    migration.drop_column("care_visit_audit", "patient_id")
    migration.drop_column("care_visit_audit", "employee_id")

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Re-add patient_id and employee_id columns to care_visit
    migration.add_column(
        table_name="care_visit",
        column_name="patient_id",
        datatype="VARCHAR(64) DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="care_visit",
        column_name="employee_id",
        datatype="VARCHAR(64) DEFAULT NULL"
    )
    
    # Re-add patient_id and employee_id columns to care_visit_audit
    migration.add_column(
        table_name="care_visit_audit",
        column_name="patient_id",
        datatype="VARCHAR(64) DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="care_visit_audit",
        column_name="employee_id",
        datatype="VARCHAR(64) DEFAULT NULL"
    )
    
    # Re-add logical_key column to patient_care_slot table
    migration.add_column(
        table_name="patient_care_slot",
        column_name="logical_key",
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    # Re-add logical_key column to patient_care_slot_audit table
    migration.add_column(
        table_name="patient_care_slot_audit",
        column_name="logical_key",
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    # Re-add logical_key column to availability_slot table
    migration.add_column(
        table_name="availability_slot",
        column_name="logical_key",
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    # Re-add logical_key column to availability_slot_audit table
    migration.add_column(
        table_name="availability_slot_audit",
        column_name="logical_key",
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    # Re-add old key columns to care_visit table
    migration.add_column(
        table_name="care_visit",
        column_name="patient_care_slot_key",
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="care_visit",
        column_name="availability_slot_key",
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    # Re-add old key columns to care_visit_audit table
    migration.add_column(
        table_name="care_visit_audit",
        column_name="patient_care_slot_key",
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="care_visit_audit",
        column_name="availability_slot_key",
        datatype="VARCHAR(255) DEFAULT NULL"
    )

    migration.update_version_table(version=down_revision)

