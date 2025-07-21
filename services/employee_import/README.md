# Employee and Physician Import Service

This service processes employee and physician CSV files uploaded to S3 and updates the respective tables in the database.

## Features

- Automatically triggered by S3 file uploads
- Parses CSV files with employee or physician data based on S3 prefix
- Upserts all records into the `employee` or `physician` table based on their respective identifiers

## Setup

The service automatically sets up:

- An SQS queue for receiving S3 notifications
- S3 bucket notifications for both employees-list/ and physicians-list/ prefixes
