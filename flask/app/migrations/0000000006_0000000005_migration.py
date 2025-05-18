revision = "0000000006"
down_revision = "0000000005"

def upgrade(migration):
    # write migration here
    migration.create_table(
        "file",
        """
            entity_id VARCHAR(32) NOT NULL,
            version VARCHAR(32) NOT NULL,
            previous_version VARCHAR(32) DEFAULT '00000000000000000000000000000000',
            active BOOLEAN DEFAULT TRUE,
            changed_by_id VARCHAR(32),
            changed_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            organization_id VARCHAR(32) NOT NULL,
            person_id VARCHAR(32) NOT NULL,
            filename VARCHAR(1024),
            s3_key TEXT,
            content_type VARCHAR(1024),
            size_bytes BIGINT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_converted BOOLEAN DEFAULT FALSE,
            source_file_id VARCHAR(1024),
            status VARCHAR(255),
            PRIMARY KEY ("entity_id")
        """
    ) 
    migration.add_index("file", "file_organization_id_ind", "organization_id")
    migration.add_index("file", "file_person_id_organization_id_ind", "person_id, organization_id")

    # Create the "person_organization_role_audit" table
    migration.create_table(
        "file_audit",
        """
            entity_id VARCHAR(32) NOT NULL,
            version VARCHAR(32) NOT NULL,
            previous_version VARCHAR(32) DEFAULT '00000000000000000000000000000000',
            active BOOLEAN DEFAULT TRUE,
            changed_by_id VARCHAR(32),
            changed_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            organization_id VARCHAR(32) NOT NULL,
            person_id VARCHAR(32) NOT NULL,
            filename VARCHAR(1024),
            s3_key TEXT,
            content_type VARCHAR(1024),
            size_bytes BIGINT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_converted BOOLEAN DEFAULT FALSE,
            source_file_id VARCHAR(1024),
            status VARCHAR(255),
            PRIMARY KEY ("entity_id", "version")
        """
    )

    migration.update_version_table(version=revision)


def downgrade(migration):
    # write migration here
    migration.drop_table(table_name="file")
    migration.drop_table(table_name="file_audit")

    migration.update_version_table(version=down_revision)
