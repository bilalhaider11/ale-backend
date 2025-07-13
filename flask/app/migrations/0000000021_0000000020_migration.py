from rococo.migrations.postgres.migration import PostgresMigration
from uuid import UUID

revision = "0000000021"
down_revision = "0000000020"


def upgrade(migration: PostgresMigration):
    # Add VersionedModel-specific fields to current_employee table
    migration.add_column(table_name="current_employee", column_name="entity_id", datatype="VARCHAR(32) DEFAULT NULL")
    migration.add_column(table_name="current_employee", column_name="version", datatype="VARCHAR(32) DEFAULT NULL")
    migration.add_column(table_name="current_employee", column_name="previous_version", datatype="VARCHAR(32) DEFAULT '00000000000000000000000000000000'")
    migration.add_column(table_name="current_employee", column_name="active", datatype="BOOLEAN DEFAULT TRUE")
    migration.add_column(table_name="current_employee", column_name="changed_by_id", datatype="VARCHAR(32) DEFAULT NULL")
    migration.add_column(table_name="current_employee", column_name="changed_on", datatype="TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP")
    
    # Populate entity_id and version for existing records
    migration.execute(f"""
        UPDATE current_employee 
        SET entity_id = REPLACE(gen_random_uuid()::text, '-', ''),
            changed_by_id = '{UUID(int=0, version=4).hex}',
        version = REPLACE(gen_random_uuid()::text, '-', '')
        WHERE entity_id IS NULL OR version IS NULL OR changed_by_id IS NULL;
    """)
    
    # Remove existing primary key constraint
    migration.remove_primary_key("current_employee")
    
    # Set entity_id and version as non-nullable
    migration.alter_column(table_name="current_employee", column_name="entity_id", datatype="VARCHAR(32)")
    migration.alter_column(table_name="current_employee", column_name="version", datatype="VARCHAR(32)")
    migration.execute("ALTER TABLE current_employee ALTER COLUMN entity_id SET NOT NULL;")
    migration.execute("ALTER TABLE current_employee ALTER COLUMN version SET NOT NULL;")
    
    # Add new primary key on entity_id
    migration.add_primary_key("current_employee", "(entity_id)")
    
    # Drop the id column
    migration.drop_column("current_employee", "id")
    
    # Create the current_employee_audit table
    migration.create_table(
        "current_employee_audit",
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
            PRIMARY KEY ("entity_id", "version")
        """
    )
    
    migration.update_version_table(version=revision)


def downgrade(migration):
    # Drop the audit table
    migration.drop_table("current_employee_audit")
    
    # Add back the id column as primary key
    migration.add_column(table_name="current_employee", column_name="id", datatype="INT AUTO_INCREMENT PRIMARY KEY")
    
    # Remove the entity_id primary key
    migration.remove_primary_key("current_employee")
    
    # Drop VersionedModel-specific columns
    migration.drop_column("current_employee", "entity_id")
    migration.drop_column("current_employee", "version")
    migration.drop_column("current_employee", "previous_version")
    migration.drop_column("current_employee", "active")
    migration.drop_column("current_employee", "changed_by_id")
    migration.drop_column("current_employee", "changed_on")
    
    migration.update_version_table(version=down_revision)
