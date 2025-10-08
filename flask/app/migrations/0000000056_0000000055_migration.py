revision = "0000000056"
down_revision = "0000000055"


def upgrade(migration):
    # Add employee_id_counter column to organization table
    migration.execute("""
        ALTER TABLE organization 
        ADD COLUMN employee_id_counter INTEGER NOT NULL DEFAULT 0
    """)
    
    # Add employee_id_counter column to organization_audit table
    migration.execute("""
        ALTER TABLE organization_audit 
        ADD COLUMN employee_id_counter INTEGER NOT NULL DEFAULT 0
    """)

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Remove employee_id_counter column from organization table
    migration.execute("""
        ALTER TABLE organization 
        DROP COLUMN IF EXISTS employee_id_counter
    """)
    
    # Remove employee_id_counter column from organization_audit table
    migration.execute("""
        ALTER TABLE organization_audit 
        DROP COLUMN IF EXISTS employee_id_counter
    """)

    migration.update_version_table(version=down_revision)

