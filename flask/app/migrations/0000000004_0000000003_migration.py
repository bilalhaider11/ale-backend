revision = "0000000004"
down_revision = "0000000003"



def upgrade(migration):
    # write migration here
    migration.create_table(
        "login_method",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "person_id" varchar(32) NOT NULL,
            "method_type" varchar(255) DEFAULT NULL,
            "method_data" text DEFAULT NULL,
            "email_id" varchar(32) DEFAULT NULL,
            "password" varchar(255) DEFAULT NULL,
            PRIMARY KEY ("entity_id")
        """
    )
    migration.add_index("login_method", "login_method_email_id_person_id_method_type_ind", "email_id, person_id, method_type")


    # Create the "login_method_audit" table
    migration.create_table(
        "login_method_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "person_id" varchar(32) NOT NULL,
            "method_type" varchar(255) DEFAULT NULL,
            "method_data" text DEFAULT NULL,
            "email_id" varchar(32) DEFAULT NULL,
            "password" varchar(255) DEFAULT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )

    migration.update_version_table(version=revision)


def downgrade(migration):
    # write migration here
    migration.drop_table(table_name="login_method")
    migration.drop_table(table_name="login_method_audit")

    migration.update_version_table(version=down_revision)
