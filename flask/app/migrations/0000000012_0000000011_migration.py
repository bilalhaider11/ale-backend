revision = "0000000012"
down_revision = "0000000011"


def upgrade(migration):
    # Add columns to employee_exclusion_match table
    migration.add_column("employee_exclusion_match", "exclusion_type", "VARCHAR(255) DEFAULT NULL")
    migration.add_column("employee_exclusion_match", "exclusion_date", "DATE DEFAULT NULL")
    migration.add_column("employee_exclusion_match", "status", "VARCHAR(50) DEFAULT NULL")
    migration.add_column("employee_exclusion_match", "match_type", "VARCHAR(50) DEFAULT NULL")
    migration.add_column("employee_exclusion_match", "employee_id", "VARCHAR(255) DEFAULT NULL")
    migration.add_column("employee_exclusion_match", "oig_exclusion_id", "VARCHAR(255) DEFAULT NULL")
    migration.add_column("employee_exclusion_match", "reviewer_notes", "TEXT DEFAULT NULL")
    
    # Add columns to employee_exclusion_match_audit table
    migration.add_column("employee_exclusion_match_audit", "exclusion_type", "VARCHAR(255) DEFAULT NULL")
    migration.add_column("employee_exclusion_match_audit", "exclusion_date", "DATE DEFAULT NULL")
    migration.add_column("employee_exclusion_match_audit", "status", "VARCHAR(50) DEFAULT NULL")
    migration.add_column("employee_exclusion_match_audit", "match_type", "VARCHAR(50) DEFAULT NULL")
    migration.add_column("employee_exclusion_match_audit", "employee_id", "VARCHAR(255) DEFAULT NULL")
    migration.add_column("employee_exclusion_match_audit", "oig_exclusion_id", "VARCHAR(255) DEFAULT NULL")
    migration.add_column("employee_exclusion_match_audit", "reviewer_notes", "TEXT DEFAULT NULL")
    
    migration.update_version_table(version=revision)


def downgrade(migration):
    # Remove columns from employee_exclusion_match table
    migration.drop_column("employee_exclusion_match", "exclusion_type")
    migration.drop_column("employee_exclusion_match", "exclusion_date")
    migration.drop_column("employee_exclusion_match", "match_type")
    migration.drop_column("employee_exclusion_match", "status")
    migration.drop_column("employee_exclusion_match", "employee_id")
    migration.drop_column("employee_exclusion_match", "oig_exclusion_id")
    migration.drop_column("employee_exclusion_match", "reviewer_notes")
    
    # Remove columns from employee_exclusion_match_audit table
    migration.drop_column("employee_exclusion_match_audit", "exclusion_type")
    migration.drop_column("employee_exclusion_match_audit", "exclusion_date")
    migration.drop_column("employee_exclusion_match_audit", "match_type")
    migration.drop_column("employee_exclusion_match_audit", "status")
    migration.drop_column("employee_exclusion_match_audit", "employee_id")
    migration.drop_column("employee_exclusion_match_audit", "oig_exclusion_id")
    migration.drop_column("employee_exclusion_match_audit", "reviewer_notes")
    
    migration.update_version_table(version=down_revision)
