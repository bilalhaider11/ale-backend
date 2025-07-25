revision = "0000000028"
down_revision = "0000000027"

def upgrade(migration):
    # PATIENT
    migration.create_table(
        "patient",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp DEFAULT CURRENT_TIMESTAMP,

            "person_id" varchar(32) DEFAULT NULL,
            "organization_id" varchar(32) DEFAULT NULL,
            "date_of_birth" date DEFAULT NULL,
            "social_security_number" varchar(255) DEFAULT NULL,

            "care_period_start" date DEFAULT NULL,
            "care_period_end" date DEFAULT NULL,
            "weekly_quota" int DEFAULT NULL,
            "current_week_remaining_quota" int DEFAULT NULL,

            PRIMARY KEY ("entity_id")
        """
    )
    migration.create_table(
        "patient_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp DEFAULT CURRENT_TIMESTAMP,

            "person_id" varchar(32) DEFAULT NULL,
            "organization_id" varchar(32) DEFAULT NULL,
            "date_of_birth" date DEFAULT NULL,
            "social_security_number" varchar(255) DEFAULT NULL,

            "care_period_start" date DEFAULT NULL,
            "care_period_end" date DEFAULT NULL,
            "weekly_quota" int DEFAULT NULL,
            "current_week_remaining_quota" int DEFAULT NULL,

            PRIMARY KEY ("entity_id","version")
        """
    )

    # PATIENT_CARE_SLOT
    migration.create_table(
        "patient_care_slot",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp DEFAULT CURRENT_TIMESTAMP,

            "patient_id" varchar(32) NOT NULL,
            "day_of_week" smallint NOT NULL,
            "start_time" time NOT NULL,
            "end_time" time NOT NULL,
            "week_start_date" date NOT NULL,
            "week_end_date" date NOT NULL,
            "is_consistent_slot" boolean DEFAULT true,

            PRIMARY KEY ("entity_id")
        """
    )
    migration.add_index("patient_care_slot", "pcs_patient_id_ind", "patient_id")
    migration.add_index("patient_care_slot", "pcs_patient_week_ind", "patient_id, week_start_date")

    migration.create_table(
        "patient_care_slot_audit",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp DEFAULT CURRENT_TIMESTAMP,

            "patient_id" varchar(32) NOT NULL,
            "day_of_week" smallint NOT NULL,
            "start_time" time NOT NULL,
            "end_time" time NOT NULL,
            "week_start_date" date NOT NULL,
            "week_end_date" date NOT NULL,
            "is_consistent_slot" boolean DEFAULT true,

            PRIMARY KEY ("entity_id")
        """
    )

    migration.update_version_table(version=revision)

def downgrade(migration):
    migration.drop_table("patient_care_slot")
    migration.drop_table("patient_care_slot_audit")
    migration.drop_table("patient")
    migration.drop_table("patient_audit")
    migration.update_version_table(version=down_revision)
