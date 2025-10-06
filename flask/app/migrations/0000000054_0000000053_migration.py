revision = "0000000054"
down_revision = "0000000053"


def upgrade(migration):
    # Add week_start_date and week_end_date columns to availability_slot table (nullable first)
    migration.add_column(
        table_name="availability_slot", 
        column_name="week_start_date", 
        datatype="date"
    )
    
    migration.add_column(
        table_name="availability_slot", 
        column_name="week_end_date", 
        datatype="date"
    )
    
    # Add week_start_date and week_end_date columns to availability_slot_audit table (nullable first)
    migration.add_column(
        table_name="availability_slot_audit", 
        column_name="week_start_date", 
        datatype="date"
    )
    
    migration.add_column(
        table_name="availability_slot_audit", 
        column_name="week_end_date", 
        datatype="date"
    )
    
    # Calculate week_start_date and week_end_date from changed_on for existing records
    # Week starts on Monday (weekday = 0)
    migration.execute("""
        UPDATE availability_slot 
        SET week_start_date = changed_on::date - INTERVAL '1 day' * EXTRACT(DOW FROM changed_on::date)::int + INTERVAL '1 day',
            week_end_date = changed_on::date - INTERVAL '1 day' * EXTRACT(DOW FROM changed_on::date)::int + INTERVAL '7 days'
        WHERE changed_on IS NOT NULL
    """)
    
    # Update audit table with the same calculation
    migration.execute("""
        UPDATE availability_slot_audit 
        SET week_start_date = changed_on::date - INTERVAL '1 day' * EXTRACT(DOW FROM changed_on::date)::int + INTERVAL '1 day',
            week_end_date = changed_on::date - INTERVAL '1 day' * EXTRACT(DOW FROM changed_on::date)::int + INTERVAL '7 days'
        WHERE changed_on IS NOT NULL
    """)
    
    # Now make the columns NOT NULL
    migration.execute("ALTER TABLE availability_slot ALTER COLUMN week_start_date SET NOT NULL")
    migration.execute("ALTER TABLE availability_slot ALTER COLUMN week_end_date SET NOT NULL")
    migration.execute("ALTER TABLE availability_slot_audit ALTER COLUMN week_start_date SET NOT NULL")
    migration.execute("ALTER TABLE availability_slot_audit ALTER COLUMN week_end_date SET NOT NULL")

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Remove week_start_date and week_end_date columns from availability_slot table
    migration.drop_column("availability_slot", "week_start_date")
    migration.drop_column("availability_slot", "week_end_date")
    migration.drop_column("availability_slot_audit", "week_start_date")
    migration.drop_column("availability_slot_audit", "week_end_date")
    
    migration.update_version_table(version=down_revision)
