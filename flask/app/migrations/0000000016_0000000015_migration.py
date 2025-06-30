revision = "0000000016"
down_revision = "0000000015"


def upgrade(migration):
    # Add social_security_number column to current_employee table
    migration.add_column(
        table_name="current_employee", 
        column_name="social_security_number", 
        datatype="VARCHAR(32) DEFAULT NULL"
    )
    
    migration.update_version_table(version=revision)


def downgrade(migration):
    # Remove social_security_number column from current_employee table
    migration.drop_column("current_employee", "social_security_number")
    
    migration.update_version_table(version=down_revision)
