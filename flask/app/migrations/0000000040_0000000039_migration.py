revision = "0000000040"
down_revision = "0000000039"


def upgrade(migration):
    # Create form_data table
    migration.execute("""
        CREATE TABLE form_data (
            entity_id VARCHAR(32) NOT NULL,
            version VARCHAR(32) NOT NULL,
            previous_version VARCHAR(32) NOT NULL DEFAULT '00000000000000000000000000000000',
            active BOOLEAN NOT NULL DEFAULT true,
            changed_by_id VARCHAR(32),
            changed_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            person_id VARCHAR(32) NOT NULL,
            form_name VARCHAR(32) NOT NULL,
            field_name VARCHAR(128) NOT NULL,
            value TEXT,
            PRIMARY KEY (entity_id, version)
        )
    """)
    
    # Create index on person_id for fast retrieval of all form data for a person
    migration.execute("""
        CREATE INDEX idx_form_data_person_id ON form_data (person_id)
    """)
    
    # Create form_data_audit table for versioning
    migration.execute("""
        CREATE TABLE form_data_audit (
            entity_id VARCHAR(32) NOT NULL,
            version VARCHAR(32) NOT NULL,
            previous_version VARCHAR(32) NOT NULL,
            active BOOLEAN NOT NULL,
            changed_by_id VARCHAR(32),
            changed_on TIMESTAMP NOT NULL,
            person_id VARCHAR(32) NOT NULL,
            form_name VARCHAR(32) NOT NULL,
            field_name VARCHAR(128) NOT NULL,
            value TEXT,
            PRIMARY KEY (entity_id, version)
        )
    """)
    
    # Create index on person_id for audit table
    migration.execute("""
        CREATE INDEX idx_form_data_audit_person_id ON form_data_audit (person_id)
    """)

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop audit table first (due to foreign key constraints)
    migration.execute("DROP TABLE IF EXISTS form_data_audit")
    
    # Drop main table
    migration.execute("DROP TABLE IF EXISTS form_data")