revision = "0000000006"
down_revision = "0000000005"

def upgrade(migration):
    migration.create_table(
        "person_organization_invitation",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            
            "organization_id" varchar(32) NOT NULL,
            "invitee_id" varchar(32) DEFAULT NULL,
            "email" varchar(128) NOT NULL,
            "roles" text NOT NULL,
            "status" varchar(32) DEFAULT 'pending',
            "first_name" varchar(128) DEFAULT NULL,
            "last_name" varchar(128) DEFAULT NULL,
            "token" text NOT NULL,
            "accepted_on" timestamp NULL,
            PRIMARY KEY ("entity_id")
        """
    )

    migration.add_index("person_organization_invitation", "poi_org_ind", "organization_id")
    migration.add_index("person_organization_invitation", "poi_email_ind", "email")
    migration.add_index("person_organization_invitation", "poi_status_ind", "status")
    migration.add_index("person_organization_invitation", "poi_token_ind", "token")

    migration.create_table(
        "person_organization_invitation_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            
            "organization_id" varchar(32) NOT NULL,
            "invitee_id" varchar(32) DEFAULT NULL,
            "email" varchar(128) NOT NULL,
            "roles" text NOT NULL,
            "status" varchar(32) DEFAULT 'pending',
            "first_name" varchar(128) DEFAULT NULL,
            "last_name" varchar(128) DEFAULT NULL,
            "token" text NOT NULL,
            "accepted_on" timestamp NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )
    migration.update_version_table(version=revision)

def downgrade(migration):
    migration.drop_table(table_name="person_organization_invitation")
    migration.drop_table(table_name="person_organization_invitation_audit")
    migration.update_version_table(version=down_revision)