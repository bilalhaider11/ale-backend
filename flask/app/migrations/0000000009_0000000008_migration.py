revision = "0000000009"
down_revision = "0000000008"

def upgrade(migration):
    migration.create_table(
        "oig_employees_exclusion",
        """
            "id" SERIAL PRIMARY KEY,
            "last_name" VARCHAR(255) DEFAULT NULL,
            "first_name" VARCHAR(255) DEFAULT NULL,
            "middle_name" VARCHAR(255) DEFAULT NULL,
            "business_name" VARCHAR(255) DEFAULT NULL,
            "general" VARCHAR(255) DEFAULT NULL,
            "specialty" VARCHAR(255) DEFAULT NULL,
            "upin" VARCHAR(16) DEFAULT NULL,
            "npi" VARCHAR(10) DEFAULT NULL,
            "date_of_birth" DATE DEFAULT NULL,
            "address" VARCHAR(255) DEFAULT NULL,
            "city" VARCHAR(100) DEFAULT NULL,
            "state" VARCHAR(2) DEFAULT NULL,
            "zip_code" VARCHAR(10) DEFAULT NULL,
            "exclusion_type" VARCHAR(16) DEFAULT NULL,
            "exclusion_date" DATE DEFAULT NULL,
            "reinstatement_date" DATE DEFAULT NULL,
            "waiver_date" DATE DEFAULT NULL,
            "waiver_state" VARCHAR(2) DEFAULT NULL
        """
    )

    migration.add_index("oig_employees_exclusion", "oig_ee_last_name_idx", "last_name")
    migration.add_index("oig_employees_exclusion", "oig_ee_first_name_idx", "first_name")
    migration.add_index("oig_employees_exclusion", "oig_ee_dob_idx", "date_of_birth")

    # Create the table to log the status of the OIG check
    # This is a VersionedModel.
    migration.create_table(
        "oig_exclusions_check",
        """
            "entity_id" VARCHAR(32) NOT NULL,
            "version" VARCHAR(32) NOT NULL,
            "previous_version" VARCHAR(32) DEFAULT '00000000000000000000000000000000',
            "active" BOOLEAN DEFAULT true,
            "changed_by_id" VARCHAR(32) DEFAULT NULL,
            "changed_on" TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            
            "status" VARCHAR(32) NOT NULL,
            "last_update_on_webpage" DATE DEFAULT NULL,
            PRIMARY KEY ("entity_id")
        """
    )

    # 3. Create the audit table for oig_exclusions_check
    migration.create_table(
        "oig_exclusions_check_audit",
        """
            "entity_id" VARCHAR(32) NOT NULL,
            "version" VARCHAR(32) NOT NULL,
            "previous_version" VARCHAR(32) DEFAULT '00000000000000000000000000000000',
            "active" BOOLEAN DEFAULT true,
            "changed_by_id" VARCHAR(32) DEFAULT NULL,
            "changed_on" TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            
            "status" VARCHAR(32) NOT NULL,
            "last_update_on_webpage" DATE DEFAULT NULL,
            PRIMARY KEY ("entity_id", "version")
        """
    )
    
    migration.update_version_table(version=revision)

def downgrade(migration):
    migration.drop_table(table_name="oig_employees_exclusion")
    migration.drop_table(table_name="oig_exclusions_check")
    migration.drop_table(table_name="oig_exclusions_check_audit")
    migration.update_version_table(version=down_revision)
