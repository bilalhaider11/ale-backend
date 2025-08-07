revision = "0000000032"
down_revision = "0000000031"


def upgrade(migration):
    # Create the "care_visit" table
    migration.create_table(
        "care_visit",
        """
            "entity_id" VARCHAR(32) NOT NULL,
            "version" VARCHAR(32) NOT NULL,
            "previous_version" VARCHAR(32) DEFAULT '00000000000000000000000000000000',
            "active" BOOLEAN DEFAULT true,
            "changed_by_id" VARCHAR(32) DEFAULT NULL,
            "changed_on" TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            "status" VARCHAR(32) NOT NULL DEFAULT 'scheduled',
            "patient_id" VARCHAR(32) NOT NULL,
            "employee_id" VARCHAR(32) NOT NULL,
            "visit_date" TIMESTAMP DEFAULT NULL,
            "scheduled_start_time" TIMESTAMP DEFAULT NULL,
            "scheduled_end_time" TIMESTAMP DEFAULT NULL,
            "clock_in_time" TIMESTAMP DEFAULT NULL,
            "clock_out_time" TIMESTAMP DEFAULT NULL,
            "scheduled_by_id" VARCHAR(32) NOT NULL,
            "availability_slot_id" VARCHAR(32) NOT NULL,
            "organization_id" VARCHAR(32) NOT NULL,
            PRIMARY KEY ("entity_id")
        """
    )

    # Create the "care_visit_audit" table
    migration.create_table(
        "care_visit_audit",
        """
            "entity_id" VARCHAR(32) NOT NULL,
            "version" VARCHAR(32) NOT NULL,
            "previous_version" VARCHAR(32) DEFAULT '00000000000000000000000000000000',
            "active" BOOLEAN DEFAULT true,
            "changed_by_id" VARCHAR(32) DEFAULT NULL,
            "changed_on" TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            "status" VARCHAR(32) NOT NULL DEFAULT 'scheduled',
            "patient_id" VARCHAR(32) NOT NULL,
            "employee_id" VARCHAR(32) NOT NULL,
            "visit_date" TIMESTAMP DEFAULT NULL,
            "scheduled_start_time" TIMESTAMP DEFAULT NULL,
            "scheduled_end_time" TIMESTAMP DEFAULT NULL,
            "clock_in_time" TIMESTAMP DEFAULT NULL,
            "clock_out_time" TIMESTAMP DEFAULT NULL,
            "scheduled_by_id" VARCHAR(32) NOT NULL,
            "availability_slot_id" VARCHAR(32) NOT NULL,
            "organization_id" VARCHAR(32) NOT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )

    # Add indexes for care_visit table
    migration.add_index("care_visit", "care_visit_visit_date_ind", "visit_date")
    migration.add_index("care_visit", "care_visit_scheduled_start_time_ind", "scheduled_start_time")
    migration.add_index("care_visit", "care_visit_scheduled_end_time_ind", "scheduled_end_time")
    migration.add_index("care_visit", "care_visit_patient_id_ind", "patient_id")
    migration.add_index("care_visit", "care_visit_employee_id_ind", "employee_id")
    migration.add_index("care_visit", "care_visit_organization_id_ind", "organization_id")

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop the tables
    migration.drop_table(table_name="care_visit")
    migration.drop_table(table_name="care_visit_audit")

    migration.update_version_table(version=down_revision)
