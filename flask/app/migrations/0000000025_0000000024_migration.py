revision = "0000000025"
down_revision = "0000000024"


def upgrade(migration):
    """
    Creates the physician and physician_audit tables.
    """
    # Create the new physician table with VersionedModel fields
    migration.create_table(
        "physician",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "national_provider_identifier" varchar(255) DEFAULT NULL,
            "date_of_birth" varchar(255) DEFAULT NULL,
            "organization_id" varchar(32) DEFAULT NULL,
            "person_id" varchar(32) DEFAULT NULL,
            PRIMARY KEY ("entity_id")
        """
    )

    # Create the physician_audit table for versioning
    migration.create_table(
        "physician_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "national_provider_identifier" varchar(255) DEFAULT NULL,
            "date_of_birth" varchar(255) DEFAULT NULL,
            "organization_id" varchar(32) DEFAULT NULL,
            "person_id" varchar(32) DEFAULT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )

    migration.update_version_table(version=revision)


def downgrade(migration):
    """
    Drops the physician and physician_audit tables.
    """
    # Drop physician tables
    migration.drop_table("physician_audit")
    migration.drop_table("physician")

    migration.update_version_table(version=down_revision)