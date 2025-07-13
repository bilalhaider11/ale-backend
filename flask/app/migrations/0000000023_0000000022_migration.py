revision = "0000000023"
down_revision = "0000000022"


def upgrade(migration):
    # Update employee_id in employee_exclusion_match table to use entity_id from employee table
    migration.execute("""
        UPDATE employee_exclusion_match eem
            SET employee_id = e.entity_id
            FROM employee e
            WHERE eem.employee_id = e.employee_id;
    """)
    
    # Update employee_id in employee_exclusion_match_audit table to use entity_id from employee table
    migration.execute("""
        UPDATE employee_exclusion_match_audit eema
            SET employee_id = e.entity_id
            FROM employee e
            WHERE eema.employee_id = e.employee_id;
    """)

    migration.update_version_table(version=revision)


def downgrade(migration):
    # This downgrade assumes we can reverse the mapping using entity_id back to employee_id
    # Note: This may not be perfectly reversible if there are data inconsistencies
    migration.execute("""
        UPDATE employee_exclusion_match eem
            SET employee_id = e.employee_id
            FROM employee e
            WHERE eem.employee_id = e.entity_id;
    """)
    
    migration.execute("""
        UPDATE employee_exclusion_match_audit eema
            SET employee_id = e.employee_id
            FROM employee e
            WHERE eema.employee_id = e.entity_id;
    """)

    migration.update_version_table(version=down_revision)
