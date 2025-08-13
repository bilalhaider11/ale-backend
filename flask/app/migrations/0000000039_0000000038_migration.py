revision = "0000000039"
down_revision = "0000000038"

def upgrade(migration):
    migration.execute("""
        ALTER TABLE patient_care_slot
        DROP COLUMN is_consistent_slot;
    """)
    
    migration.execute("""
        ALTER TABLE patient_care_slot_audit
        DROP COLUMN is_consistent_slot;
    """)
    
    migration.update_version_table(version=revision)

def downgrade(migration):
    migration.execute("""
        ALTER TABLE patient_care_slot
        ADD COLUMN is_consistent_slot boolean DEFAULT true;
    """)
    
    migration.execute("""
        ALTER TABLE patient_care_slot_audit
        ADD COLUMN is_consistent_slot boolean DEFAULT true;
    """)
    
    migration.update_version_table(version=down_revision)
