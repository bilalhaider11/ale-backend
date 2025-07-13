revision = "0000000022"
down_revision = "0000000021"


def upgrade(migration):
    # Create the new employee table with VersionedModel fields
    migration.create_table(
        "employee",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "primary_branch" varchar(255) DEFAULT NULL,
            "employee_id" varchar(255) DEFAULT NULL,
            "first_name" varchar(255) DEFAULT NULL,
            "last_name" varchar(255) DEFAULT NULL,
            "suffix" varchar(255) DEFAULT NULL,
            "employee_type" varchar(255) DEFAULT NULL,
            "user_type" varchar(100) DEFAULT NULL,
            "address_1" varchar(255) DEFAULT NULL,
            "address_2" varchar(255) DEFAULT NULL,
            "city" varchar(255) DEFAULT NULL,
            "state" varchar(255) DEFAULT NULL,
            "zip_code" varchar(20) DEFAULT NULL,
            "email_address" varchar(255) DEFAULT NULL,
            "phone_1" varchar(50) DEFAULT NULL,
            "phone_2" varchar(50) DEFAULT NULL,
            "payroll_start_date" DATE DEFAULT NULL,
            "hire_date" DATE DEFAULT NULL,
            "date_of_birth" DATE DEFAULT NULL,
            "organization_id" varchar(32) DEFAULT NULL,
            "caregiver_tags" text DEFAULT NULL,
            "social_security_number" varchar(255) DEFAULT NULL,
            "person_id" varchar(32) DEFAULT NULL,
            PRIMARY KEY ("entity_id")
        """
    )
    
    # Insert data from current_employee into employee table
    migration.execute("""
        INSERT INTO employee (
            entity_id, version, previous_version, active, changed_by_id, changed_on,
            primary_branch, employee_id, first_name, last_name, suffix, employee_type,
            user_type, address_1, address_2, city, state, zip_code, email_address,
            phone_1, phone_2, payroll_start_date, hire_date, date_of_birth,
            organization_id, caregiver_tags, social_security_number, person_id
        )
        SELECT 
            entity_id, version, previous_version, active, changed_by_id, changed_on,
            primary_branch, employee_id, first_name, last_name, suffix, employee_type,
            user_type, address_1, address_2, city, state, zip_code, email_address,
            phone_1, phone_2, payroll_start_date, hire_date, date_of_birth,
            organization_id, caregiver_tags, social_security_number, person_id
        FROM current_employee
    """)
    
    # Rename current_employee_audit table to employee_audit
    migration.change_table_name("current_employee_audit", "employee_audit")
    
    # Drop the old current_employee table
    migration.drop_table("current_employee")
    
    migration.update_version_table(version=revision)


def downgrade(migration):
    # Create the current_employee table back
    migration.create_table(
        "current_employee",
        """
            "entity_id" varchar(32) NOT NULL,
            "version" varchar(32) NOT NULL,
            "previous_version" varchar(32) DEFAULT '00000000000000000000000000000000',
            "active" boolean DEFAULT true,
            "changed_by_id" varchar(32) DEFAULT NULL,
            "changed_on" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
            "primary_branch" varchar(255) DEFAULT NULL,
            "employee_id" varchar(255) DEFAULT NULL,
            "first_name" varchar(255) DEFAULT NULL,
            "last_name" varchar(255) DEFAULT NULL,
            "suffix" varchar(255) DEFAULT NULL,
            "employee_type" varchar(255) DEFAULT NULL,
            "user_type" varchar(255) DEFAULT NULL,
            "address_1" varchar(255) DEFAULT NULL,
            "address_2" varchar(255) DEFAULT NULL,
            "city" varchar(255) DEFAULT NULL,
            "state" varchar(255) DEFAULT NULL,
            "zip_code" varchar(255) DEFAULT NULL,
            "email_address" varchar(255) DEFAULT NULL,
            "phone_1" varchar(255) DEFAULT NULL,
            "phone_2" varchar(255) DEFAULT NULL,
            "payroll_start_date" varchar(255) DEFAULT NULL,
            "hire_date" varchar(255) DEFAULT NULL,
            "date_of_birth" varchar(255) DEFAULT NULL,
            "organization_id" varchar(32) DEFAULT NULL,
            "caregiver_tags" text DEFAULT NULL,
            "social_security_number" varchar(255) DEFAULT NULL,
            "person_id" varchar(32) DEFAULT NULL,
            PRIMARY KEY ("entity_id")
        """
    )
    
    # Insert data back from employee into current_employee table
    migration.execute("""
        INSERT INTO current_employee (
            entity_id, version, previous_version, active, changed_by_id, changed_on,
            primary_branch, employee_id, first_name, last_name, suffix, employee_type,
            user_type, address_1, address_2, city, state, zip_code, email_address,
            phone_1, phone_2, payroll_start_date, hire_date, date_of_birth,
            organization_id, caregiver_tags, social_security_number, person_id
        )
        SELECT 
            entity_id, version, previous_version, active, changed_by_id, changed_on,
            primary_branch, employee_id, first_name, last_name, suffix, employee_type,
            user_type, address_1, address_2, city, state, zip_code, email_address,
            phone_1, phone_2, payroll_start_date, hire_date, date_of_birth,
            organization_id, caregiver_tags, social_security_number, person_id
        FROM employee
    """)
    
    # Rename employee_audit table back to current_employee_audit
    migration.change_table_name("employee_audit", "current_employee_audit")
    
    # Drop the employee table
    migration.drop_table("employee")
    
    migration.update_version_table(version=down_revision)
