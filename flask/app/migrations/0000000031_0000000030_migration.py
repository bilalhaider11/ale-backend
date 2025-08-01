revision = "0000000031"
down_revision = "0000000030"


def upgrade(migration):
    # Create the "organization_partnership" table
    migration.create_table(
        "organization_partnership",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "requesting_organization_id" varchar(32) DEFAULT NULL,
            "organization_1_id" varchar(32) DEFAULT NULL,
            "organization_2_id" varchar(32) DEFAULT NULL,
            "status" varchar(255) DEFAULT NULL,
            "message" TEXT DEFAULT NULL,
            "requested_by_id" varchar(32) DEFAULT NULL,
            "responded_by_id" varchar(32) DEFAULT NULL,
            "created_at" timestamp NULL DEFAULT NULL,
            PRIMARY KEY ("entity_id")
        """
    )

    # Create the "organization_partnership_audit" table
    migration.create_table(
        "organization_partnership_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "requesting_organization_id" varchar(32) DEFAULT NULL,
            "organization_1_id" varchar(32) DEFAULT NULL,
            "organization_2_id" varchar(32) DEFAULT NULL,
            "status" varchar(255) DEFAULT NULL,
            "message" TEXT DEFAULT NULL,
            "requested_by_id" varchar(32) DEFAULT NULL,
            "responded_by_id" varchar(32) DEFAULT NULL,
            "created_at" timestamp NULL DEFAULT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop the tables
    migration.drop_table(table_name="organization_partnership")
    migration.drop_table(table_name="organization_partnership_audit")

    migration.update_version_table(version=down_revision)
