revision = "0000000017"
down_revision = "0000000016"


def upgrade(migration):
    # Create the "current_employees_file" table
    migration.create_table(
        "current_employees_file",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "organization_id" varchar(32) DEFAULT NULL,
            "file_name" varchar(255) DEFAULT NULL,
            "file_size" int DEFAULT NULL,
            "file_type" varchar(50) DEFAULT NULL,
            "s3_key" varchar(1024) DEFAULT NULL,
            "uploaded_at" timestamp NULL DEFAULT NULL,
            "uploaded_by" varchar(32) DEFAULT NULL,
            "status" varchar(50) DEFAULT NULL,
            "error_message" text DEFAULT NULL,
            "record_count" int DEFAULT NULL,
            PRIMARY KEY ("entity_id")
        """
    )

    # Create the "current_employees_file_audit" table
    migration.create_table(
        "current_employees_file_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "organization_id" varchar(32) DEFAULT NULL,
            "file_name" varchar(255) DEFAULT NULL,
            "file_size" int DEFAULT NULL,
            "file_type" varchar(50) DEFAULT NULL,
            "s3_key" varchar(1024) DEFAULT NULL,
            "uploaded_at" timestamp NULL DEFAULT NULL,
            "uploaded_by" varchar(32) DEFAULT NULL,
            "status" varchar(50) DEFAULT NULL,
            "error_message" text DEFAULT NULL,
            "record_count" int DEFAULT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop the tables
    migration.drop_table(table_name="current_employees_file")
    migration.drop_table(table_name="current_employees_file_audit")

    migration.update_version_table(version=down_revision)
