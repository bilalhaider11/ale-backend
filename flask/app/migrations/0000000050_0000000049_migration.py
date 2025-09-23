revision = "0000000050"
down_revision = "0000000049"


def upgrade(migration):
    # Fix the primary key constraint on patient_care_slot_audit table
    # The audit table should have a composite primary key (entity_id, version)
    # instead of just (entity_id) to allow multiple versions of the same entity
    
    # Drop the existing primary key constraint
    migration.execute("ALTER TABLE patient_care_slot_audit DROP CONSTRAINT patient_care_slot_audit_pkey")
    
    # Add the correct composite primary key constraint
    migration.execute("ALTER TABLE patient_care_slot_audit ADD CONSTRAINT patient_care_slot_audit_pkey PRIMARY KEY (entity_id, version)")

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Revert to the incorrect primary key constraint
    migration.execute("ALTER TABLE patient_care_slot_audit DROP CONSTRAINT patient_care_slot_audit_pkey")
    migration.execute("ALTER TABLE patient_care_slot_audit ADD CONSTRAINT patient_care_slot_audit_pkey PRIMARY KEY (entity_id)")

    migration.update_version_table(version=down_revision)
