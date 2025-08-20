revision = "0000000042"
down_revision = "0000000041"

def upgrade(migration):
    migration.create_table(
        "phone_number",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp DEFAULT CURRENT_TIMESTAMP,
            "person_id" varchar(32) NOT NULL,
            "phone" varchar(255) NOT NULL,
            PRIMARY KEY ("entity_id")
        """
    )
    migration.create_table(
        "phone_number_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp DEFAULT CURRENT_TIMESTAMP,
            "person_id" varchar(32) NOT NULL,
            "phone" varchar(255) NOT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )
    migration.add_index("phone_number", "phone_number_person_id_idx", "person_id")
    migration.update_version_table(version=revision)

def downgrade(migration):
    migration.drop_table("phone_number")
    migration.drop_table("phone_number_audit")
    migration.update_version_table(version=down_revision)