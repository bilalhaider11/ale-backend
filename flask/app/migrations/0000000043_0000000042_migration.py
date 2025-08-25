from rococo.migrations.postgres.migration import PostgresMigration

revision = "0000000043"
down_revision = "0000000042"

def upgrade(migration: PostgresMigration):
    """Refresh the database collation version to match the current system ICU library"""
    with migration.db_adapter:
        try:
            # Get current db name and collation version in one query
            initial_state_query = """
                SELECT datname, datcollversion 
                FROM pg_database 
                WHERE datname = current_database();
            """
            result = migration.db_adapter.execute_query(initial_state_query)
            
            if not result:
                raise Exception("Could not retrieve current database information.")

            # Handle different return formats (dict or list/tuple)
            if isinstance(result[0], dict):
                db_name = result[0]['datname']
                old_version = result[0]['datcollversion']
            else:
                db_name = result[0][0]
                old_version = result[0][1]

            print(f"Database: '{db_name}', Initial collation version: {old_version}")

            # Execute the collation version refresh
            # refresh_sql = f'ALTER DATABASE "{db_name}" REFRESH COLLATION VERSION;'
            refresh_sql = f'ALTER DATABASE "rococo-sample-db" REFRESH COLLATION VERSION;'
            migration.db_adapter.execute_query(refresh_sql)
            
            # Verify the collation version was updated by running the same query again
            new_result = migration.db_adapter.execute_query(initial_state_query)
            
            if new_result:
                new_version = new_result[0]['datcollversion'] if isinstance(new_result[0], dict) else new_result[0][1]
                if old_version != new_version:
                    print(f"  🎉 Collation version successfully updated from {old_version} to {new_version}")
                else:
                    print(f"  ℹ️ Collation version remains {new_version}. No update was needed.")

            # Update the migration version to mark this as completed
            migration.update_version_table(version=revision)

        except Exception as _e:
            import traceback
            print(f"  Traceback: {traceback.format_exc()}")
            raise

def downgrade(migration):
    """Note: Collation version refresh cannot be reversed"""
    with migration.db_adapter:
        migration.update_version_table(version=down_revision)
