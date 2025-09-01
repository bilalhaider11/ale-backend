revision = "0000000044"
down_revision = "0000000043"

def upgrade(migration):
    # Add gender and date_of_birth columns to person and person_audit tables
    migration.add_column("person", "gender", "varchar(50) DEFAULT NULL")
    migration.add_column("person", "date_of_birth", "date DEFAULT NULL")
    migration.add_column("person_audit", "gender", "varchar(50) DEFAULT NULL")
    migration.add_column("person_audit", "date_of_birth", "date DEFAULT NULL")

    migration.update_version_table(version=revision)

def downgrade(migration):
    # Remove columns from person and person_audit tables
    migration.drop_column("person", "gender")
    migration.drop_column("person", "date_of_birth")
    migration.drop_column("person_audit", "gender")
    migration.drop_column("person_audit", "date_of_birth")

    migration.update_version_table(version=down_revision)
