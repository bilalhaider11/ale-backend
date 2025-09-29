revision = "0000000052"
down_revision = "0000000051"


def upgrade(migration):
    # Add start_day_of_week and end_day_of_week columns to patient_care_slot table (nullable first)
    migration.add_column(
        table_name="availability_slot",
        column_name="start_day_of_week",
        datatype="smallint"
    )

    migration.add_column(
        table_name="availability_slot",
        column_name="end_day_of_week",
        datatype="smallint"
    )

    # Add start_day_of_week and end_day_of_week columns to patient_care_slot_audit table (nullable first)
    migration.add_column(
        table_name="availability_slot_audit",
        column_name="start_day_of_week",
        datatype="smallint"
    )

    migration.add_column(
        table_name="availability_slot_audit",
        column_name="end_day_of_week",
        datatype="smallint"
    )

    # Update existing records to set start_day_of_week and end_day_of_week to day_of_week value
    migration.execute("UPDATE availability_slot SET start_day_of_week = day_of_week, end_day_of_week = day_of_week")
    migration.execute(
        "UPDATE availability_slot_audit SET start_day_of_week = day_of_week, end_day_of_week = day_of_week")

    # Now make the columns NOT NULL
    migration.execute("ALTER TABLE availability_slot ALTER COLUMN start_day_of_week SET NOT NULL")
    migration.execute("ALTER TABLE availability_slot ALTER COLUMN end_day_of_week SET NOT NULL")
    migration.execute("ALTER TABLE availability_slot_audit ALTER COLUMN start_day_of_week SET NOT NULL")
    migration.execute("ALTER TABLE availability_slot_audit ALTER COLUMN end_day_of_week SET NOT NULL")

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Remove start_day_of_week and end_day_of_week columns from patient_care_slot table
    migration.drop_column("availability_slot", "start_day_of_week")
    migration.drop_column("availability_slot", "end_day_of_week")

    # Remove start_day_of_week and end_day_of_week columns from patient_care_slot_audit table
    migration.drop_column("availability_slot_audit", "start_day_of_week")
    migration.drop_column("availability_slot_audit", "end_day_of_week")

    migration.update_version_table(version=down_revision)
