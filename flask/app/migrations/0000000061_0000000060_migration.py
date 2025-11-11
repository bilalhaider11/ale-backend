revision = "0000000061"
down_revision = "0000000060"

def upgrade(migration):
    # Add patient_mrn_counter column to organization table
    migration.execute("""
        ALTER TABLE organization 
        ADD COLUMN patient_mrn_counter INTEGER NOT NULL DEFAULT 0
    """)
    
    # Add patient_mrn_counter column to organization_audit table
    migration.execute("""
        ALTER TABLE organization_audit 
        ADD COLUMN patient_mrn_counter INTEGER NOT NULL DEFAULT 0
    """)

    migration.update_version_table(version=revision)

def downgrade(migration):
    # Remove patient_mrn_counter column from organization table
    migration.execute("""
        ALTER TABLE organization 
        DROP COLUMN IF EXISTS patient_mrn_counter
    """)
    
    # Remove patient_mrn_counter column from organization_audit table
    migration.execute("""
        ALTER TABLE organization_audit 
        DROP COLUMN IF EXISTS patient_mrn_counter
    """)

    migration.update_version_table(version=down_revision)

