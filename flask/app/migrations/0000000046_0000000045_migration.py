revision = "0000000046"
down_revision = "0000000045"

def upgrade(migration):
    # Add verification_result column to employee_exclusion_match table
    migration.add_column("employee_exclusion_match", "verification_result", "VARCHAR(100) DEFAULT NULL")
    
    # Add s3_key column to employee_exclusion_match table
    migration.add_column("employee_exclusion_match", "s3_key", "VARCHAR(500) DEFAULT NULL")
    
    # Add verification_result column to employee_exclusion_match_audit table
    migration.add_column("employee_exclusion_match_audit", "verification_result", "VARCHAR(100) DEFAULT NULL")
    
    # Add s3_key column to employee_exclusion_match_audit table
    migration.add_column("employee_exclusion_match_audit", "s3_key", "VARCHAR(500) DEFAULT NULL")

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop verification_result column from employee_exclusion_match table
    migration.drop_column("employee_exclusion_match", "verification_result")
    
    # Drop s3_key column from employee_exclusion_match table
    migration.drop_column("employee_exclusion_match", "s3_key")
    
    # Drop verification_result column from employee_exclusion_match_audit table
    migration.drop_column("employee_exclusion_match_audit", "verification_result")
    
    # Drop s3_key column from employee_exclusion_match_audit table
    migration.drop_column("employee_exclusion_match_audit", "s3_key")

    migration.update_version_table(version=down_revision) 