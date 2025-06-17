# Employee Exclusion Match Service

This service processes messages to check for matches between current employees/caregivers and the OIG exclusion list.

## Purpose

The service receives messages via RabbitMQ and performs the following operations:
1. Queries current employees and caregivers from the database
2. Matches them against the OIG exclusion list using case-insensitive name comparison and exact date of birth matching
3. Updates the employee_exclusion_match table with the results

## Dependencies

- RabbitMQ for message processing
- PostgreSQL database with the following tables:
  - `current_employee`
  - `current_caregiver` 
  - `oig_employees_exclusion`
  - `employee_exclusion_match`

## Usage

The service runs as a Docker container and processes messages automatically when they are received from the configured RabbitMQ queue.
