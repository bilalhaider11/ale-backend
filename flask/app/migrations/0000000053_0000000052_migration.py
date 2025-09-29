revision = "0000000053"
down_revision = "0000000052"


def upgrade(migration):
    # Update form_name values in form_data table
    migration.execute("""
        UPDATE form_data 
        SET form_name = 'NEW_HIRE_INITIAL_CONTACT' 
        WHERE form_name = 'EMPLOYMENT_APPLICATION'
    """)

    migration.execute("""
        UPDATE form_data 
        SET form_name = 'SFC_NEW_HIRE_INITIAL_CONTACT' 
        WHERE form_name = 'SFC_EMPLOYMENT_APPLICATION'
    """)

    migration.execute("""
        UPDATE form_data 
        SET form_name = 'FINANCIALS' 
        WHERE form_name = 'DIRECT_DEPOSIT_AUTHORIZATION'
    """)

    migration.execute("""
        UPDATE form_data 
        SET form_name = 'SFC_FINANCIALS' 
        WHERE form_name = 'DIRECT_DEPOSIT_SFC_AUTHORIZATION'
    """)

    migration.execute("""
        UPDATE form_data 
        SET form_name = 'NEW_HIRE_PAPERWORK' 
        WHERE form_name = 'CONFIDENTIALITY_NONCOMPETE_AGR'
    """)

    # Also update the same values in the audit table
    migration.execute("""
        UPDATE form_data_audit 
        SET form_name = 'NEW_HIRE_INITIAL_CONTACT' 
        WHERE form_name = 'EMPLOYMENT_APPLICATION'
    """)

    migration.execute("""
        UPDATE form_data_audit 
        SET form_name = 'SFC_NEW_HIRE_INITIAL_CONTACT' 
        WHERE form_name = 'SFC_EMPLOYMENT_APPLICATION'
    """)

    migration.execute("""
        UPDATE form_data_audit 
        SET form_name = 'FINANCIALS' 
        WHERE form_name = 'DIRECT_DEPOSIT_AUTHORIZATION'
    """)

    migration.execute("""
        UPDATE form_data_audit 
        SET form_name = 'SFC_FINANCIALS' 
        WHERE form_name = 'DIRECT_DEPOSIT_SFC_AUTHORIZATION'
    """)

    migration.execute("""
        UPDATE form_data_audit 
        SET form_name = 'NEW_HIRE_PAPERWORK' 
        WHERE form_name = 'CONFIDENTIALITY_NONCOMPETE_AGR'
    """)

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Restore original form_name values
    migration.execute("""
        UPDATE form_data 
        SET form_name = 'EMPLOYMENT_APPLICATION' 
        WHERE form_name = 'NEW_HIRE_INITIAL_CONTACT'
    """)

    migration.execute("""
        UPDATE form_data 
        SET form_name = 'SFC_EMPLOYMENT_APPLICATION' 
        WHERE form_name = 'SFC_NEW_HIRE_INITIAL_CONTACT'
    """)

    migration.execute("""
        UPDATE form_data 
        SET form_name = 'DIRECT_DEPOSIT_AUTHORIZATION' 
        WHERE form_name = 'FINANCIALS'
    """)

    migration.execute("""
        UPDATE form_data 
        SET form_name = 'DIRECT_DEPOSIT_SFC_AUTHORIZATION' 
        WHERE form_name = 'SFC_FINANCIALS'
    """)

    migration.execute("""
        UPDATE form_data 
        SET form_name = 'CONFIDENTIALITY_NONCOMPETE_AGR' 
        WHERE form_name = 'NEW_HIRE_PAPERWORK'
    """)

    # Also restore original values in the audit table
    migration.execute("""
        UPDATE form_data_audit 
        SET form_name = 'EMPLOYMENT_APPLICATION' 
        WHERE form_name = 'NEW_HIRE_INITIAL_CONTACT'
    """)

    migration.execute("""
        UPDATE form_data_audit 
        SET form_name = 'SFC_EMPLOYMENT_APPLICATION' 
        WHERE form_name = 'SFC_NEW_HIRE_INITIAL_CONTACT'
    """)

    migration.execute("""
        UPDATE form_data_audit 
        SET form_name = 'DIRECT_DEPOSIT_AUTHORIZATION' 
        WHERE form_name = 'FINANCIALS'
    """)

    migration.execute("""
        UPDATE form_data_audit 
        SET form_name = 'DIRECT_DEPOSIT_SFC_AUTHORIZATION' 
        WHERE form_name = 'SFC_FINANCIALS'
    """)

    migration.execute("""
        UPDATE form_data_audit 
        SET form_name = 'CONFIDENTIALITY_NONCOMPETE_AGR' 
        WHERE form_name = 'NEW_HIRE_PAPERWORK'
    """)

    migration.update_version_table(version=down_revision)