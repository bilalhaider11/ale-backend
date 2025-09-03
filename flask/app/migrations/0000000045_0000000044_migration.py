revision = "0000000045"
down_revision = "0000000046"

def upgrade(migration):
    # Move date_of_birth from patient to person table
    migration.execute("""
        UPDATE person p
        SET date_of_birth = pt.date_of_birth
        FROM patient pt
        WHERE p.entity_id = pt.person_id
        AND pt.date_of_birth IS NOT NULL
    """)
    
    # Add column to patient and patient_audit tables
    migration.add_column("patient", "medical_record_number", "varchar(255) DEFAULT NULL")
    migration.add_column("patient_audit", "medical_record_number", "varchar(255) DEFAULT NULL")
    
    # Copy data from social_security_number to medical_record_number
    migration.execute("""
        UPDATE patient
        SET medical_record_number = social_security_number
        WHERE social_security_number IS NOT NULL
    """)
    
    # Drop columns from patient and patient_audit tables
    migration.drop_column("patient", "social_security_number")
    migration.drop_column("patient_audit", "social_security_number")
    migration.drop_column("patient", "date_of_birth")
    migration.drop_column("patient_audit", "date_of_birth")
    
    migration.update_version_table(version=revision)

def downgrade(migration):

    # Add columns back to patient table
    migration.add_column("patient", "date_of_birth", "date DEFAULT NULL")
    migration.add_column("patient_audit", "date_of_birth", "date DEFAULT NULL")
    migration.add_column("patient", "social_security_number", "varchar(255) DEFAULT NULL")
    migration.add_column("patient_audit", "social_security_number", "varchar(255) DEFAULT NULL")

    migration.execute("""
        UPDATE patient
        SET social_security_number = medical_record_number
        WHERE medical_record_number IS NOT NULL
    """)

    # Remove column from patient and patient_audit tables
    migration.drop_column("patient", "medical_record_number")
    migration.drop_column("patient_audit", "medical_record_number")

    # Copy date_of_birth data from person back to patient
    migration.execute("""
        UPDATE patient pt
        SET date_of_birth = p.date_of_birth
        FROM person p
        WHERE p.entity_id = pt.person_id
        AND p.date_of_birth IS NOT NULL
    """)
    
    migration.update_version_table(version=down_revision)
