import uuid

revision = "0000000038"
down_revision = "0000000037"


def upgrade(migration):
    # Reset care_visit table
    migration.execute(f"""
        DELETE FROM care_visit;    
    """)

    migration.update_version_table(version=revision)


def downgrade(migration):
    migration.update_version_table(version=down_revision)
