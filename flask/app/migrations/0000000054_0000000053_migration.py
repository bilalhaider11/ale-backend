revision = "0000000054"
down_revision = "0000000053"


def upgrade(migration):
    # Add series_id columns
    migration.add_column(
        table_name="patient_care_slot",
        column_name="series_id",
        datatype="VARCHAR(64) DEFAULT NULL"
    )

    migration.add_column(
        table_name="patient_care_slot_audit",
        column_name="series_id",
        datatype="VARCHAR(64) DEFAULT NULL"
    )

    migration.add_column(
        table_name="availability_slot",
        column_name="series_id",
        datatype="VARCHAR(64) DEFAULT NULL"
    )

    migration.add_column(
        table_name="availability_slot_audit",
        column_name="series_id",
        datatype="VARCHAR(64) DEFAULT NULL"
    )

    migration.execute("""
        CREATE INDEX idx_patient_care_slot_series_date
        ON patient_care_slot(patient_id, series_id, start_date)
        WHERE active = true;
    """)

    migration.execute("""
        CREATE INDEX idx_availability_slot_series_date
        ON availability_slot(employee_id, series_id, start_date)
        WHERE active = true;
    """)

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop series_id columns
    migration.drop_column("patient_care_slot", "series_id")
    migration.drop_column("patient_care_slot_audit", "series_id")
    migration.drop_column("availability_slot", "series_id")
    migration.drop_column("availability_slot_audit", "series_id")

    migration.execute("DROP INDEX IF EXISTS idx_patient_care_slot_series_date;")
    migration.execute("DROP INDEX IF EXISTS idx_availability_slot_series_date;")

    migration.update_version_table(version=down_revision)
