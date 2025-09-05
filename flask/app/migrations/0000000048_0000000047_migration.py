revision = "0000000048"
down_revision = "0000000047"


def upgrade(migration):
    # Add longitude and latitude columns to care_visit table for clock_in location
    migration.add_column(
        table_name="care_visit", 
        column_name="clock_in_longitude", 
        datatype="DOUBLE PRECISION DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="care_visit", 
        column_name="clock_in_latitude", 
        datatype="DOUBLE PRECISION DEFAULT NULL"
    )
    
    # Add longitude and latitude columns to care_visit table for clock_out location
    migration.add_column(
        table_name="care_visit", 
        column_name="clock_out_longitude", 
        datatype="DOUBLE PRECISION DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="care_visit", 
        column_name="clock_out_latitude", 
        datatype="DOUBLE PRECISION DEFAULT NULL"
    )
    
    # Add longitude and latitude columns to care_visit_audit table for clock_in location
    migration.add_column(
        table_name="care_visit_audit", 
        column_name="clock_in_longitude", 
        datatype="DOUBLE PRECISION DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="care_visit_audit", 
        column_name="clock_in_latitude", 
        datatype="DOUBLE PRECISION DEFAULT NULL"
    )
    
    # Add longitude and latitude columns to care_visit_audit table for clock_out location
    migration.add_column(
        table_name="care_visit_audit", 
        column_name="clock_out_longitude", 
        datatype="DOUBLE PRECISION DEFAULT NULL"
    )
    
    migration.add_column(
        table_name="care_visit_audit", 
        column_name="clock_out_latitude", 
        datatype="DOUBLE PRECISION DEFAULT NULL"
    )

    migration.update_version_table(version=revision)


def downgrade(migration):
    # Remove longitude and latitude columns from care_visit table
    migration.drop_column("care_visit", "clock_in_longitude")
    migration.drop_column("care_visit", "clock_in_latitude")
    migration.drop_column("care_visit", "clock_out_longitude")
    migration.drop_column("care_visit", "clock_out_latitude")
    
    # Remove longitude and latitude columns from care_visit_audit table
    migration.drop_column("care_visit_audit", "clock_in_longitude")
    migration.drop_column("care_visit_audit", "clock_in_latitude")
    migration.drop_column("care_visit_audit", "clock_out_longitude")
    migration.drop_column("care_visit_audit", "clock_out_latitude")

    migration.update_version_table(version=down_revision)
