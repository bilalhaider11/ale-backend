revision = "0000000024"
down_revision = "0000000023"


def upgrade(migration):
    # Create the "availability_slot" table
    migration.create_table(
        "availability_slot",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "day_of_week" int NOT NULL,
            "start_time" time NOT NULL,
            "end_time" time NOT NULL,
            "employee_id" varchar(32) NOT NULL,
            PRIMARY KEY ("entity_id")
        """
    )
    migration.add_index("availability_slot", "availability_slot_employee_id_ind", "employee_id")
    migration.add_index("availability_slot", "availability_slot_day_of_week_ind", "day_of_week")

    # Create the "availability_slot_audit" table
    migration.create_table(
        "availability_slot_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "day_of_week" int NOT NULL,
            "start_time" time NOT NULL,
            "end_time" time NOT NULL,
            "employee_id" varchar(32) NOT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )
    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop the tables
    migration.drop_table(table_name="availability_slot")
    migration.drop_table(table_name="availability_slot_audit")

    migration.update_version_table(version=down_revision)
