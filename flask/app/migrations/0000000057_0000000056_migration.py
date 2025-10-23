revision = "0000000057"
down_revision = "0000000056"


def upgrade(migration):

    migration.execute("""
        ALTER TABLE care_visit 
        drop column patient_care_slot_key
    """)
    
    migration.execute("""
        ALTER TABLE care_visit
        drop column availability_slot_key
    """)

    migration.update_version_table(version=revision)


def downgrade(migration):
    migration.execute("""
        ALTER TABLE care_visit 
        add column patient_care_slot_key varchar(255)
    """)
    
    migration.execute("""
        ALTER TABLE care_visit
        add column availability_slot_key varchar(255)
    """)

    migration.update_version_table(version=down_revision)

