revision = "0000000010"
down_revision = "0000000009"

def upgrade(migration):
    # Create the updated table with new fields
    migration.create_table(
        "current_employee",
        """
            "id" SERIAL PRIMARY KEY,
            "primary_branch" VARCHAR(255) DEFAULT NULL,
            "employee_id" VARCHAR(255) DEFAULT NULL,
            "first_name" VARCHAR(255) DEFAULT NULL,
            "last_name" VARCHAR(255) DEFAULT NULL,
            "suffix" VARCHAR(50) DEFAULT NULL,
            "employee_type" VARCHAR(100) DEFAULT NULL,
            "user_type" VARCHAR(100) DEFAULT NULL,
            "address_1" VARCHAR(255) DEFAULT NULL,
            "address_2" VARCHAR(255) DEFAULT NULL,
            "city" VARCHAR(100) DEFAULT NULL,
            "state" VARCHAR(50) DEFAULT NULL,
            "zip_code" VARCHAR(20) DEFAULT NULL,
            "email_address" VARCHAR(255) DEFAULT NULL,
            "phone_1" VARCHAR(50) DEFAULT NULL,
            "phone_2" VARCHAR(50) DEFAULT NULL,
            "payroll_start_date" DATE DEFAULT NULL,
            "hire_date" DATE DEFAULT NULL,
            "date_of_birth" DATE DEFAULT NULL
        """
    )

    # Add indexes
    migration.add_index("current_employee", "current_employee_first_name_idx", "first_name")
    migration.add_index("current_employee", "current_employee_last_name_idx", "last_name")
    migration.add_index("current_employee", "current_employee_dob_idx", "date_of_birth")
    
    # Create the caregiver table
    migration.create_table(
        "current_caregiver",
        """
            "id" SERIAL PRIMARY KEY,
            "caregiver_id" VARCHAR(255) DEFAULT NULL,
            "first_name" VARCHAR(255) DEFAULT NULL,
            "last_name" VARCHAR(255) DEFAULT NULL,
            "address" VARCHAR(255) DEFAULT NULL,
            "city" VARCHAR(100) DEFAULT NULL,
            "state" VARCHAR(50) DEFAULT NULL,
            "postal_code" VARCHAR(20) DEFAULT NULL,
            "hire_date" DATE DEFAULT NULL,
            "caregiver_tags" VARCHAR(255) DEFAULT NULL,
            "email" VARCHAR(255) DEFAULT NULL,
            "date_of_birth" DATE DEFAULT NULL
        """
    )

    # Add indexes for caregiver
    migration.add_index("current_caregiver", "current_caregiver_first_name_idx", "first_name")
    migration.add_index("current_caregiver", "current_caregiver_last_name_idx", "last_name")
    migration.add_index("current_caregiver", "current_caregiver_dob_idx", "date_of_birth")
    
    migration.update_version_table(version=revision)

def downgrade(migration):
    # Drop the updated tables
    migration.drop_table(table_name="current_employee")
    migration.drop_table(table_name="current_caregiver")
    migration.update_version_table(version=down_revision)
