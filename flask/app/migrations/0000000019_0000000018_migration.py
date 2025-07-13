revision = "0000000019"
down_revision = "0000000018"


def upgrade(migration):
    # Add person_id column to current_employee table
    migration.add_column(table_name="current_employee", column_name="person_id", datatype="VARCHAR(32) DEFAULT NULL")
    
    migration.update_version_table(version=revision)


def downgrade(migration):
    # Remove person_id column from current_employee table
    migration.drop_column("current_employee", "person_id")
    
    migration.update_version_table(version=down_revision)
