revision = "0000000029"
down_revision = "0000000028"

def upgrade(migration):
    """
    Creates the patients_file and patients_file_audit tables.
    """
    migration.create_table(
        "patients_file",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,

            "organization_id" varchar(32) DEFAULT NULL,
            "file_name" varchar(255) DEFAULT NULL,
            "file_size" bigint DEFAULT NULL,
            "file_type" varchar(100) DEFAULT NULL,
            "s3_key" varchar(500) DEFAULT NULL,
            "uploaded_at" timestamp NULL DEFAULT NULL,
            "uploaded_by" varchar(32) DEFAULT NULL,
            "status" varchar(50) DEFAULT 'pending',
            "error_message" text DEFAULT NULL,
            "record_count" int DEFAULT NULL,

            PRIMARY KEY ("entity_id")
        """
    )
    
    # Add indexes for common queries
    migration.add_index("patients_file", "patients_file_organization_id_ind", "organization_id")
    migration.add_index("patients_file", "patients_file_status_ind", "status")
    migration.add_index("patients_file", "patients_file_uploaded_at_ind", "uploaded_at")
    
    migration.create_table(
        "patients_file_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,

            "organization_id" varchar(32) DEFAULT NULL,
            "file_name" varchar(255) DEFAULT NULL,
            "file_size" bigint DEFAULT NULL,
            "file_type" varchar(100) DEFAULT NULL,
            "s3_key" varchar(500) DEFAULT NULL,
            "uploaded_at" timestamp NULL DEFAULT NULL,
            "uploaded_by" varchar(32) DEFAULT NULL,
            "status" varchar(50) DEFAULT 'pending',
            "error_message" text DEFAULT NULL,
            "record_count" int DEFAULT NULL,

            PRIMARY KEY ("entity_id", "version")
        """
    )

    migration.update_version_table(version=revision)

def downgrade(migration):
    """
    Removes the patients_file and patients_file_audit tables.
    """
    migration.drop_table(table_name="patients_file")
    migration.drop_table(table_name="patients_file_audit")

    migration.update_version_table(version=down_revision)
