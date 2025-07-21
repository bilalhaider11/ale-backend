from rococo.migrations.postgres.migration import PostgresMigration

revision = "0000000027"
down_revision = "0000000026"


def upgrade(migration: PostgresMigration):
    """
    Adds the file_category column to the current_employees_file
    and its audit table.
    """
    # Add the file_category column to the main table
    migration.add_column(
        table_name="current_employees_file",
        column_name="file_category",
        datatype="VARCHAR(255)"
    )

    # Also add the file_category column to the audit table
    migration.add_column(
        table_name="current_employees_file_audit",
        column_name="file_category",
        datatype="VARCHAR(255)"
    )

    # Update the migration version in the database
    migration.update_version_table(version=revision)


def downgrade(migration: PostgresMigration):
    """
    Removes the file_category column from the current_employees_file
    and its audit table.
    """
    # Drop the file_category column from the main table
    migration.drop_column(
        table_name="current_employees_file",
        column_name="file_category"
    )

    # Also drop the file_category column from the audit table
    migration.drop_column(
        table_name="current_employees_file_audit",
        column_name="file_category"
    )

    # Revert the migration version in the database
    migration.update_version_table(version=down_revision)