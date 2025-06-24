revision = "0000000014"
down_revision = "0000000013"


def upgrade(migration):
    # Add organization_id column to current_employee table
    migration.add_column(
        table_name="current_employee",
        column_name="organization_id",
        datatype="VARCHAR(32) NULL"
    )

    # Add organization_id column to current_employee table
    migration.add_column(
        table_name="current_employee",
        column_name="caregiver_tags",
        datatype="TEXT NULL"
    )

    # Add organization_id column to employee_exclusion_match table
    migration.add_column(
        table_name="employee_exclusion_match",
        column_name="organization_id",
        datatype="VARCHAR(32) NULL"
    )

    # Add organization_id column to employee_exclusion_match table
    migration.add_column(
        table_name="employee_exclusion_match_audit",
        column_name="organization_id",
        datatype="VARCHAR(32) NULL"
    )

    migration.add_index(
        table_name="current_employee",
        index_name="idx_current_employee_name_dob_organization_id",
        indexed_column="first_name, last_name, date_of_birth, organization_id"
    )

    migration.add_index(
        table_name="employee_exclusion_match",
        index_name="idx_employee_exclusion_match_organization_id",
        indexed_column="organization_id"
    )
    
    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop organization_id column from current_employee and employee_exclusion_match table
    migration.drop_column("current_employee", "organization_id")
    migration.drop_column("current_employee", "caregiver_tags")
    migration.drop_column("employee_exclusion_match", "organization_id")
    migration.drop_column("employee_exclusion_match_audit", "organization_id")

    migration.update_version_table(version=down_revision)
