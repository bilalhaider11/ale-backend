from rococo.migrations.postgres.migration import PostgresMigration

revision = "0000000026"
down_revision = "0000000025"

def upgrade(migration: PostgresMigration):
    """
    Generalizes employee matching by replacing employee_id with
    a generic matched_entity_type and matched_entity_id.
    """
    # Add new generic columns to the main table
    migration.add_column(
        table_name="employee_exclusion_match",
        column_name="matched_entity_type",
        datatype="varchar(50)"
    )
    migration.add_column(
        table_name="employee_exclusion_match",
        column_name="matched_entity_id",
        datatype="varchar(32)"
    )

    # Add new generic columns to the audit table
    migration.add_column(
        table_name="employee_exclusion_match_audit",
        column_name="matched_entity_type",
        datatype="varchar(50)"
    )
    migration.add_column(
        table_name="employee_exclusion_match_audit",
        column_name="matched_entity_id",
        datatype="varchar(32)"
    )

    # Migrate existing data from employee_id to the new generic columns
    # for the main table.
    migration.execute("""
        UPDATE employee_exclusion_match
        SET matched_entity_type = 'employee',
            matched_entity_id = employee_id
        WHERE employee_id IS NOT NULL
    """)

    # Migrate existing data for the audit table.
    migration.execute("""
        UPDATE employee_exclusion_match_audit
        SET matched_entity_type = 'employee',
            matched_entity_id = employee_id
        WHERE employee_id IS NOT NULL
    """)

    # Drop the old employee_id column from both tables
    migration.drop_column("employee_exclusion_match", "employee_id")
    migration.drop_column("employee_exclusion_match_audit", "employee_id")

    # Update the migration version in the database
    migration.update_version_table(version=revision)


def downgrade(migration: PostgresMigration):
    """
    Reverts the generalization by removing matched_entity columns
    and restoring the employee_id column.
    """
    # Add back the specific employee_id column to both tables
    migration.add_column(
        table_name="employee_exclusion_match",
        column_name="employee_id",
        datatype="varchar(32)"
    )
    migration.add_column(
        table_name="employee_exclusion_match_audit",
        column_name="employee_id",
        datatype="varchar(32)"
    )

    # Migrate data back from generic columns to the employee_id column
    # for the main table.
    migration.execute("""
        UPDATE employee_exclusion_match
        SET employee_id = matched_entity_id
        WHERE matched_entity_type = 'employee'
    """)

    # Migrate data back for the audit table.
    migration.execute("""
        UPDATE employee_exclusion_match_audit
        SET employee_id = matched_entity_id
        WHERE matched_entity_type = 'employee'
    """)

    # Drop the generic columns from both tables
    migration.drop_column("employee_exclusion_match", "matched_entity_type")
    migration.drop_column("employee_exclusion_match", "matched_entity_id")
    migration.drop_column("employee_exclusion_match_audit", "matched_entity_type")
    migration.drop_column("employee_exclusion_match_audit", "matched_entity_id")

    # Revert the migration version in the database
    migration.update_version_table(version=down_revision)
