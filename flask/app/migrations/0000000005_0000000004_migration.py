revision = "0000000005"
down_revision = "0000000004"



def upgrade(migration):
    # write migration here
    migration.create_table(
        "person_organization_role",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "person_id" varchar(32) NOT NULL,
            "organization_id" varchar(32) NOT NULL,
            "role" varchar(32) DEFAULT NULL,
            PRIMARY KEY ("entity_id")
        """
    )
    migration.add_index("person_organization_role", "person_organization_role_person_id_ind", "person_id")
    migration.add_index("person_organization_role", "person_organization_role_organization_id_ind", "organization_id")
    migration.add_index("person_organization_role", "person_organization_role_person_id_organization_id_ind", "person_id, organization_id")

    # Create the "person_organization_role_audit" table
    migration.create_table(
        "person_organization_role_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "person_id" varchar(32) NOT NULL,
            "organization_id" varchar(32) NOT NULL,
            "role" varchar(32) DEFAULT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )

    migration.update_version_table(version=revision)


def downgrade(migration):
    # write migration here
    migration.drop_table(table_name="person_organization_role")
    migration.drop_table(table_name="person_organization_role_audit")

    migration.update_version_table(version=down_revision)
