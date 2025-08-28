revision = "0000000044"
down_revision = "0000000043"


def upgrade(migration):
    # Add s3_key column to employee_exclusion_match table
    migration.add_column("employee_exclusion_match", "s3_key", "VARCHAR(500) DEFAULT NULL")
    
    # Add s3_key column to employee_exclusion_match_audit table
    migration.add_column("employee_exclusion_match_audit", "s3_key", "VARCHAR(500) DEFAULT NULL")

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop s3_key column from employee_exclusion_match table
    migration.drop_column("employee_exclusion_match", "s3_key")
    
    # Drop s3_key column from employee_exclusion_match_audit table
    migration.drop_column("employee_exclusion_match_audit", "s3_key")

    migration.update_version_table(version=down_revision) 