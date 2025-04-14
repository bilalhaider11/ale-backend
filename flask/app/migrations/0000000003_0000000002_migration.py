revision = "0000000003"
down_revision = "0000000002"



def upgrade(migration):
    # write migration here
    migration.create_table(
        "email",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "person_id" varchar(32) NOT NULL,
            "email" varchar(254) DEFAULT NULL,
            "is_verified" boolean DEFAULT NULL,
            "is_default" boolean DEFAULT NULL,
            PRIMARY KEY ("entity_id")
        """
    )
    migration.add_index("email", "email_email_ind", "email")
    migration.add_index("email", "email_person_id_ind", "person_id")


    # Create the "email_audit" table
    migration.create_table(
        "email_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "person_id" varchar(32) NOT NULL,
            "email" varchar(254) DEFAULT NULL,
            "is_verified" boolean DEFAULT NULL,
            "is_default" boolean DEFAULT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )

    migration.update_version_table(version=revision)


def downgrade(migration):
    # write migration here
    migration.drop_table(table_name="email")
    migration.drop_table(table_name="email_audit")

    migration.update_version_table(version=down_revision)
