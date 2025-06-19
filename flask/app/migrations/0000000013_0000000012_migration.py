revision = "0000000013"
down_revision = "0000000012"


def upgrade(migration):
    # Add reviewer_id column to employee_exclusion_match table
    migration.add_column(
        table_name="employee_exclusion_match", 
        column_name="reviewer_id", 
        datatype="VARCHAR(255) NULL"
    )
    
    # Add reviewer_name column to employee_exclusion_match table
    migration.add_column(
        table_name="employee_exclusion_match", 
        column_name="reviewer_name", 
        datatype="VARCHAR(255) NULL"
    )

    # Add review_date column to employee_exclusion_match table
    migration.add_column(
        table_name="employee_exclusion_match", 
        column_name="review_date", 
        datatype="DATE DEFAULT NULL"
    )
    
    # Add reviewer_id column to employee_exclusion_match_audit table
    migration.add_column(
        table_name="employee_exclusion_match_audit", 
        column_name="reviewer_id", 
        datatype="VARCHAR(255) NULL"
    )

    # Add reviewer_name column to employee_exclusion_match_audit table
    migration.add_column(
        table_name="employee_exclusion_match_audit", 
        column_name="reviewer_name", 
        datatype="VARCHAR(255) NULL"
    )
    
    # Add review_date column to employee_exclusion_match_audit table
    migration.add_column(
        table_name="employee_exclusion_match_audit", 
        column_name="review_date", 
        datatype="DATE DEFAULT NULL"
    )
    
    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop reviewer_id column from employee_exclusion_match table
    migration.drop_column("employee_exclusion_match", "reviewer_id")
    
    # Drop review_date column from employee_exclusion_match table
    migration.drop_column("employee_exclusion_match", "review_date")
    
    # Drop reviewer_id column from employee_exclusion_match_audit table
    migration.drop_column("employee_exclusion_match_audit", "reviewer_id")
    
    # Drop review_date column from employee_exclusion_match_audit table
    migration.drop_column("employee_exclusion_match_audit", "review_date")
    
    migration.update_version_table(version=down_revision)
