revision = "0000000051"
down_revision = "0000000050"



def upgrade(migration):
    # write migration here
    migration.add_column(
        table_name="patient_care_slot",
        column_name="start_date",
        datatype="DATE DEFAULT NULL"
    )

    migration.add_column(
        table_name="patient_care_slot",
        column_name="end_date",
        datatype="DATE DEFAULT NULL"
    )

    migration.add_column(
        table_name="patient_care_slot_audit",
        column_name="start_date",
        datatype="DATE DEFAULT NULL"
    )

    migration.add_column(
        table_name="patient_care_slot_audit",
        column_name="end_date",
        datatype="DATE DEFAULT NULL"
    )

    migration.add_column(
        table_name="availability_slot",
        column_name="start_date",
        datatype="DATE DEFAULT NULL"
    )

    migration.add_column(
        table_name="availability_slot",
        column_name="end_date",
        datatype="DATE DEFAULT NULL"
    )

    migration.add_column(
        table_name="availability_slot_audit",
        column_name="start_date",
        datatype="DATE DEFAULT NULL"
    )

    migration.add_column(
        table_name="availability_slot_audit",
        column_name="end_date",
        datatype="DATE DEFAULT NULL"
    )

    migration.update_version_table(version=revision)


def downgrade(migration):
    # remove columns from patient_care_slot
    migration.drop_column("patient_care_slot", "start_date")
    migration.drop_column("patient_care_slot", "end_date")

    # remove columns from patient_care_slot_audit
    migration.drop_column("patient_care_slot_audit", "start_date")
    migration.drop_column("patient_care_slot_audit", "end_date")

    # remove columns from availability_slot
    migration.drop_column("availability_slot", "start_date")
    migration.drop_column("availability_slot", "end_date")

    # remove columns from availability_slot_audit
    migration.drop_column("availability_slot_audit", "start_date")
    migration.drop_column("availability_slot_audit", "end_date")

    # set migration version back
    migration.update_version_table(version=down_revision)


