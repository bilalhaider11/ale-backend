revision = "0000000001"
down_revision = "0000000000"



def upgrade(migration):
    # write migration here
    migration.create_table(
        "organization",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "name" varchar(128) NOT NULL,
            "code" varchar(16) DEFAULT NULL,
            "description" TEXT DEFAULT NULL,
            PRIMARY KEY ("entity_id")
        """
    )
    migration.add_index("organization", "organization_name_ind", "name")

    # Create the "organization_audit" table
    migration.create_table(
        "organization_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "name" varchar(128) NOT NULL,
            "code" varchar(16) DEFAULT NULL,
            "description" TEXT DEFAULT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )
    migration.update_version_table(version=revision)


def downgrade(migration):
    # write migration here
    migration.drop_table(table_name="organization")
    migration.drop_table(table_name="organization_audit")

    migration.update_version_table(version=down_revision)
