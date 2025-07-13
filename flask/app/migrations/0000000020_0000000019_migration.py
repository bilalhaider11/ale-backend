revision = "0000000020"
down_revision = "0000000019"

from uuid import UUID


def upgrade(migration):
    # Generate UUIDs and create person records for current_employees without employee_id
    migration.execute("""
        UPDATE current_employee 
        SET person_id = REPLACE(gen_random_uuid()::text, '-', '') 
        WHERE person_id IS NULL;
    """)
    
    # Upsert person records for current_employees
    migration.execute(f"""
        INSERT INTO person (
            entity_id, 
            version, 
            previous_version, 
            active, 
            changed_by_id, 
            changed_on, 
            first_name, 
            last_name
        )
        SELECT 
            ce.person_id,
            REPLACE(gen_random_uuid()::text, '-', ''),
            '{UUID(int=0).hex}',
            true,
            '{UUID(int=0, version=4).hex}',
            NOW(),
            ce.first_name,
            ce.last_name
        FROM current_employee ce
        WHERE ce.person_id IS NOT NULL
        ON CONFLICT (entity_id)
        DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name;
    """)
    
    migration.update_version_table(version=revision)


def downgrade(migration):
    # Remove person records that were created for current_employees without employee_id
    migration.execute_sql("""
        DELETE p FROM person p
        INNER JOIN current_employee ce ON p.entity_id = ce.person_id
        WHERE ce.employee_id IS NULL
    """)
    
    # Clear person_id from current_employee records that had null employee_id
    migration.execute_sql("""
        UPDATE current_employee 
        SET person_id = NULL 
        WHERE employee_id IS NULL
    """)
    
    migration.update_version_table(version=down_revision)
