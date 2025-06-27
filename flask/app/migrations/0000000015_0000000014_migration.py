revision = "0000000015"
down_revision = "0000000014"

def upgrade(migration):
    migration.execute("""
    UPDATE organization
    SET logo_url = REPLACE(logo_url, 'https://d3gqrv1stsrtwc.cloudfront.net/', '')
    WHERE logo_url LIKE 'https://d3gqrv1stsrtwc.cloudfront.net/%%';
    """)
    
    migration.execute("""
    UPDATE organization_audit
    SET logo_url = REPLACE(logo_url, 'https://d3gqrv1stsrtwc.cloudfront.net/', '')
    WHERE logo_url LIKE 'https://d3gqrv1stsrtwc.cloudfront.net/%%';
    """)
    
    migration.update_version_table(version=revision)

def downgrade(migration):
    migration.update_version_table(version=down_revision)