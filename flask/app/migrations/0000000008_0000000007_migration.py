revision = "0000000008"
down_revision = "0000000007"

def upgrade(migration):
    migration.execute("""
    ALTER TABLE organization
    ADD COLUMN IF NOT EXISTS logo_url TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS subdomain TEXT DEFAULT NULL;
    """)
    migration.execute("""
    ALTER TABLE organization_audit
    ADD COLUMN IF NOT EXISTS logo_url TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS subdomain TEXT DEFAULT NULL;
    """)
    migration.update_version_table(version=revision)

def downgrade(migration):
    migration.execute("""
    ALTER TABLE organization
    DROP COLUMN IF EXISTS logo_url,
    DROP COLUMN IF EXISTS subdomain;
    """)
    migration.execute("""
    ALTER TABLE organization_audit
    DROP COLUMN IF EXISTS logo_url,
    DROP COLUMN IF EXISTS subdomain;
    """)
    migration.update_version_table(version=down_revision)