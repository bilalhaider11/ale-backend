revision = "0000000011"
down_revision = "0000000010"


def upgrade(migration):
    # Create the "employee_exclusion_match" table
    migration.create_table(
        "employee_exclusion_match",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "first_name" varchar(255) DEFAULT NULL,
            "last_name" varchar(255) DEFAULT NULL,
            "date_of_birth" date DEFAULT NULL,
            PRIMARY KEY ("entity_id")
        """
    )

    # Create the "employee_exclusion_match_audit" table
    migration.create_table(
        "employee_exclusion_match_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "first_name" varchar(255) DEFAULT NULL,
            "last_name" varchar(255) DEFAULT NULL,
            "date_of_birth" date DEFAULT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop the tables
    migration.drop_table(table_name="employee_exclusion_match")
    migration.drop_table(table_name="employee_exclusion_match_audit")

    migration.update_version_table(version=down_revision)
