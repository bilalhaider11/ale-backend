import uuid

revision = "0000000037"
down_revision = "0000000036"


def upgrade(migration):
    # Get all employees with NULL person_id
    employees_without_person = migration.execute("""
        SELECT entity_id, first_name, last_name, changed_by_id
        FROM employee 
        WHERE person_id IS NULL AND active = true
    """)
    
    for employee in employees_without_person:
        employee_id = employee['entity_id']
        first_name = (employee['first_name'] or "")[:128]
        last_name = (employee['last_name'] or "")[:128]
        changed_by_id = employee['changed_by_id'] or ""
        
        # Generate a new entity_id for the person record
        person_entity_id = str(uuid.uuid4()).replace('-', '')
        person_version = str(uuid.uuid4()).replace('-', '')
        
        # Insert person record
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
            ) VALUES (
                %s, 
                %s, 
                '00000000000000000000000000000000', 
                true, 
                %s, 
                CURRENT_TIMESTAMP, 
                %s, 
                %s
            )
        """, args=(person_entity_id, person_version, changed_by_id, first_name, last_name))
        
        # Update employee record with the new person_id
        migration.execute(f"""
            UPDATE employee 
            SET person_id = %s 
            WHERE entity_id = %s
        """, args=(person_entity_id, employee_id))

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Get all employees that were updated in this migration
    # We'll identify them by finding employees whose person records have matching first/last names
    migration.execute("""
        UPDATE employee e
        JOIN person p ON e.person_id = p.entity_id
        SET e.person_id = NULL
        WHERE e.first_name = p.first_name AND e.last_name = p.last_name
    """)
    
    # Delete the person records that were created in this migration
    migration.execute("""
        DELETE p FROM person p
        JOIN employee e ON p.entity_id = e.person_id
        WHERE e.first_name = p.first_name AND e.last_name = p.last_name
    """)
    
    # Delete the person audit records
    migration.execute("""
        DELETE pa FROM person_audit pa
        JOIN employee e ON pa.entity_id = e.person_id
        WHERE e.first_name = pa.first_name AND e.last_name = pa.last_name
    """)

    migration.update_version_table(version=down_revision)
