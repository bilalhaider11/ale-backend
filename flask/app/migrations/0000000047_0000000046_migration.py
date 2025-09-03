revision = "0000000047"
down_revision = "0000000046"

def upgrade(migration):
    migration.create_table(
        "alert",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "organization_id" varchar(32) NOT NULL,
            "level" integer NOT NULL,
            "area" varchar(128) NOT NULL,
            "message" text NOT NULL,
            "status" integer NOT NULL DEFAULT 0,
            "assigned_to_id" varchar(32) DEFAULT NULL,
            "handled_at_start" timestamp NULL DEFAULT NULL,
            "handled_at_end" timestamp NULL DEFAULT NULL,
            "created_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY ("entity_id")
        """
    )
    migration.add_index("alert", "alert_organization_id_idx", "organization_id")
    migration.add_index("alert", "alert_assigned_to_id_idx", "assigned_to_id")
    migration.add_index("alert", "alert_status_idx", "status")
    migration.add_index("alert", "alert_level_idx", "level")

    migration.create_table(
        "alert_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "organization_id" varchar(32) NOT NULL,
            "level" integer NOT NULL,
            "area" varchar(128) NOT NULL,
            "message" text NOT NULL,
            "status" integer NOT NULL DEFAULT 0,
            "assigned_to_id" varchar(32) DEFAULT NULL,
            "handled_at_start" timestamp NULL DEFAULT NULL,
            "handled_at_end" timestamp NULL DEFAULT NULL,
            "created_at" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY ("entity_id", "version")
        """
    )

    migration.create_table(
        "alert_person",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "alert_id" varchar(32) NOT NULL,
            "person_id" varchar(32) NOT NULL,
            "read" boolean NOT NULL DEFAULT false,
            PRIMARY KEY ("entity_id")
        """
    )
    migration.add_index("alert_person", "alert_person_alert_id_idx", "alert_id")
    migration.add_index("alert_person", "alert_person_person_id_idx", "person_id")
    migration.add_index("alert_person", "alert_person_unique_idx", "alert_id, person_id")

    migration.create_table(
        "alert_person_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "alert_id" varchar(32) NOT NULL,
            "person_id" varchar(32) NOT NULL,
            "read" boolean NOT NULL DEFAULT false,
            PRIMARY KEY ("entity_id", "version")
        """
    )

    migration.update_version_table(version=revision)


def downgrade(migration):
    migration.drop_table(table_name="alert_person")
    migration.drop_table(table_name="alert_person_audit")
    migration.drop_table(table_name="alert")
    migration.drop_table(table_name="alert_audit")

    migration.update_version_table(version=down_revision)
