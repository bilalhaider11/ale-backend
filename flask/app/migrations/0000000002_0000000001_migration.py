revision = "0000000002"
down_revision = "0000000001"



def upgrade(migration):
    # write migration here
    migration.create_table(
        "person",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "first_name" varchar(128) DEFAULT NULL,
            "last_name" varchar(128) DEFAULT NULL,
            PRIMARY KEY ("entity_id")
        """
    )

    # Create the "person_audit" table
    migration.create_table(
        "person_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "first_name" varchar(128) DEFAULT NULL,
            "last_name" varchar(128) DEFAULT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )
    migration.update_version_table(version=revision)


def downgrade(migration):
    # write migration here
    migration.drop_table(table_name="person")
    migration.drop_table(table_name="person_audit")

    migration.update_version_table(version=down_revision)
