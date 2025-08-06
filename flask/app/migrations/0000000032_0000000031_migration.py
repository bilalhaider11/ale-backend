revision = "0000000032"
down_revision = "0000000031"

def upgrade(migration):
    migration.execute("""
    ALTER TABLE patient 
    ADD COLUMN care_duration float DEFAULT NULL;
    """)
    
    migration.execute("""
    UPDATE patient 
    SET care_duration = current_week_remaining_quota;
    """)
    
    migration.execute("""
    ALTER TABLE patient 
    DROP COLUMN current_week_remaining_quota;
    """)
    
    migration.execute("""
    ALTER TABLE patient_audit 
    ADD COLUMN care_duration float DEFAULT NULL;
    """)
    
    migration.execute("""
    UPDATE patient_audit 
    SET care_duration = current_week_remaining_quota;
    """)
    
    migration.execute("""
    ALTER TABLE patient_audit 
    DROP COLUMN current_week_remaining_quota;
    """)
    
    migration.update_version_table(version=revision)

def downgrade(migration):
    migration.execute("""
    ALTER TABLE patient 
    ADD COLUMN current_week_remaining_quota int DEFAULT NULL;
    """)
    
    migration.execute("""
    UPDATE patient 
    SET current_week_remaining_quota = CAST(care_duration AS integer);
    """)
    
    migration.execute("""
    ALTER TABLE patient 
    DROP COLUMN care_duration;
    """)
    
    migration.execute("""
    ALTER TABLE patient_audit 
    ADD COLUMN current_week_remaining_quota int DEFAULT NULL;
    """)
    
    migration.execute("""
    UPDATE patient_audit 
    SET current_week_remaining_quota = CAST(care_duration AS integer);
    """)
    
    migration.execute("""
    ALTER TABLE patient_audit 
    DROP COLUMN care_duration;
    """)
    
    migration.update_version_table(version=down_revision)
