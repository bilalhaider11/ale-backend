revision = "0000000018"
down_revision = "0000000017"


def upgrade(migration):
    # Delete data from the "current_employees_file" table
    migration.execute("DELETE FROM current_employees_file;")
    migration.execute("DELETE FROM current_employees_file_audit;")

    # Delete data from the "current_employees" table
    migration.execute("DELETE FROM current_employee;")

    # Delete data from the "employee_exclusion_match" table
    migration.execute("DELETE FROM employee_exclusion_match;")
    migration.execute("DELETE FROM employee_exclusion_match_audit;")

    migration.update_version_table(version=revision)


def downgrade(migration):

    migration.update_version_table(version=down_revision)
