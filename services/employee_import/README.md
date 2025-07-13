# Employee Import Service

This service processes employee and caregiver CSV files uploaded to S3 and updates the respective tables in the database.

## Features

- Automatically triggered by S3 file uploads
- Parses CSV files with employee or caregiver data based on S3 prefix
- Upserts all records into the `employee` table based on (first_name, last_name, employee_id) tuple.

## Setup

The service automatically sets up:

- An SQS queue for receiving S3 notifications
- S3 bucket notifications for both employees-list/ and caregivers-list/ prefixes
