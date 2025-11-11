revision = "0000000060"
down_revision = "0000000059"

#patient care slot

def upgrade(migration):
    
    # Drop availability_slot_key column from care_visit table
    
    migration.drop_column("patient_care_slot", "day_of_week")
    
    migration.drop_column("patient_care_slot", "week_start_date")
    
    migration.drop_column("patient_care_slot", "week_end_date")
    
    migration.drop_column("patient_care_slot", "logical_key")
    
    migration.drop_column("patient_care_slot_audit", "day_of_week")
    
    migration.drop_column("patient_care_slot_audit", "week_start_date")
    
    migration.drop_column("patient_care_slot_audit", "week_end_date")
    
    migration.drop_column("patient_care_slot_audit", "logical_key")
    
    migration.update_version_table(version=revision)


def downgrade(migration):
    
    migration.add_column(
        table_name="patient_care_slot",
        column_name="day_of_week",
        datatype="SMALLINT DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="patient_care_slot",
        column_name="week_start_date",
        datatype="DATE DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="patient_care_slot",
        column_name="week_end_date",
        datatype="DATE DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="patient_care_slot",
        column_name="logical_key",
        datatype="VARCHAR(255) DEFAULT NULL"
    )
   
    migration.add_column(
        table_name="patient_care_slot_audit",
        column_name="day_of_week",
        datatype="SMALLINT DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="patient_care_slot_audit",
        column_name="week_start_date",
        datatype="DATE DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="patient_care_slot_audit",
        column_name="week_end_date",
        datatype="DATE DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="patient_care_slot_audit",
        column_name="logical_key",
        datatype="VARCHAR(255) DEFAULT NULL"
    )
    
    
    migration.update_version_table(version=down_revision)
