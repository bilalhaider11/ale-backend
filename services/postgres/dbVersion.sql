-- Create the db_version table only if it does not exist
CREATE TABLE IF NOT EXISTS db_version (
    version VARCHAR(10) NOT NULL
);

-- Insert the default version only if it does not already exist
INSERT INTO db_version (version)
SELECT '0000000000'
WHERE NOT EXISTS (SELECT 1 FROM db_version);
