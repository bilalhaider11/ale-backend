# OIG Update Check Service

This service checks for updates to the OIG LEIE (List of Excluded Individuals/Entities) database and imports new data when available.

## Purpose

The service runs daily to:

1. Check the OIG website for the "Last Update" date
2. Compare with the last successful import date
3. Download and import new CSV data if an update is available
4. Log all check results for audit purposes

## Configuration

The service runs as a CRON job daily at 2:00 AM UTC. This can be configured in the Dockerfile by modifying the `CRON_RUN_AT` environment variable.

## Database Tables

- `oig_employees_exclusion`: Stores the OIG LEIE data (truncated and repopulated on each import)
- `oig_exclusions_check`: Logs each check execution with status and metadata

## Status Values

- `imported`: Update was available and successfully imported
- `import_failed`: Update was available but import failed
- `no_update`: No update was available
- `check_failed`: Could not determine if update was available
