revision = "0000000041"
down_revision = "0000000040"


def upgrade(migration):
    # Create fax_template table
    migration.execute("""
        CREATE TABLE fax_template (
            entity_id VARCHAR(32) NOT NULL,
            version VARCHAR(32) NOT NULL,
            previous_version VARCHAR(32) NOT NULL DEFAULT '00000000000000000000000000000000',
            active BOOLEAN NOT NULL DEFAULT true,
            changed_by_id VARCHAR(32),
            changed_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            name VARCHAR(255) NOT NULL,
            body TEXT NOT NULL,
            organization_id VARCHAR(32) NOT NULL,
            PRIMARY KEY (entity_id, version)
        )
    """)
    
    # Create index on organization_id for fast retrieval of all templates for an organization
    migration.execute("""
        CREATE INDEX idx_fax_template_organization_id ON fax_template (organization_id)
    """)
    
    # Create index on name for alphabetical sorting
    migration.execute("""
        CREATE INDEX idx_fax_template_name ON fax_template (name)
    """)
    
    # Create fax_template_audit table for versioning
    migration.execute("""
        CREATE TABLE fax_template_audit (
            entity_id VARCHAR(32) NOT NULL,
            version VARCHAR(32) NOT NULL,
            previous_version VARCHAR(32) NOT NULL,
            active BOOLEAN NOT NULL,
            changed_by_id VARCHAR(32),
            changed_on TIMESTAMP NOT NULL,
            name VARCHAR(255) NOT NULL,
            body TEXT NOT NULL,
            organization_id VARCHAR(32) NOT NULL,
            PRIMARY KEY (entity_id, version)
        )
    """)
    
    # Create index on organization_id for audit table
    migration.execute("""
        CREATE INDEX idx_fax_template_audit_organization_id ON fax_template_audit (organization_id)
    """)

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop audit table first (due to foreign key constraints)
    migration.execute("DROP TABLE IF EXISTS fax_template_audit")
    
    # Drop main table
    migration.execute("DROP TABLE IF EXISTS fax_template")
