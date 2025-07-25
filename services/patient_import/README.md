# Patient Import Service

This service processes patient CSV and XLSX files uploaded to S3 and updates the patient table in the database.

## Features

- Automatically triggered by S3 file uploads
- Parses CSV and XLSX files with patient data based on S3 prefix
- Upserts all records into the `patient` table based on their identifiers

## Setup

The service automatically sets up:

- An SQS queue for receiving S3 notifications
- S3 bucket notifications for patients-list/ prefix
