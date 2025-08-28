# OIG Verifier Service

This service processes exclusion matches and performs automated OIG verification using web scraping when matches are found between employees/caregivers and the OIG exclusion list.

## Purpose

The service receives messages via RabbitMQ when exclusion matches are found and performs the following operations:
1. Receives match data from the employee exclusion match service
2. Retrieves employee SSN from the database
3. Performs automated OIG verification using Selenium web scraping
4. Updates match status based on verification results (Match/No Match/Error)
5. Stores verification results and screenshots for audit purposes

## Features

- **Automated OIG Verification**: Uses Selenium WebDriver to automatically verify employees on the OIG exclusions website
- **Screenshot Capture**: Takes screenshots at each step of the verification process for audit trails
- **SSN Validation**: Validates SSN format before attempting verification
- **Error Handling**: Comprehensive error handling with detailed logging
- **Status Updates**: Updates match records with verification results

## Dependencies

- RabbitMQ for message processing
- PostgreSQL database with the following tables:
  - `employee_exclusion_match`
  - `employee`
  - `oig_employees_exclusion`
- Chrome browser and ChromeDriver for Selenium automation
- Selenium WebDriver for web automation

## Environment Variables

- `SELENIUM_HOST`: Hostname for Selenium Grid (default: localhost)
- `SELENIUM_PORT`: Port for Selenium Grid (default: 4444)

## Usage

The service runs as a Docker container and processes messages automatically when they are received from the configured RabbitMQ queue.

### Local Development

For local development, the service will use the local Chrome installation. Make sure Chrome is installed on your system.

### Docker/Production

The Docker container includes Chrome and all necessary dependencies for headless operation.

## Message Format

The service expects messages in the following format:
```json
{
  "action": "verify_matches",
  "source": "employee_exclusion_match_service",
  "matches": [
    {
      "entity_id": "match_id",
      "matched_entity_id": "employee_id",
      "matched_entity_type": "employee",
      "organization_id": "org_id",
      "first_name": "John",
      "last_name": "Doe",
      "date_of_birth": "1990-01-01",
      "match_type": "name_and_dob"
    }
  ]
}
```

## Verification Process

1. **Name Search**: Searches the OIG website using the employee's first and last name
2. **SSN Verification**: If matches are found, verifies the employee's SSN against the exclusion record
3. **Result Processing**: Determines if there's a match or no match based on the verification
4. **Status Update**: Updates the database record with the verification result

## Verification Results

- **Match**: Employee is confirmed to be on the OIG exclusion list
- **No Match**: Employee is not on the OIG exclusion list or SSN doesn't match
- **Error**: Technical error occurred during verification
- **Skipped**: Verification was skipped (e.g., no SSN available)

## Screenshots

Screenshots are automatically captured during the verification process and stored in organized directories with timestamps for audit purposes.

## Logging

Comprehensive logging is provided at each step of the verification process, including:
- Message processing details
- Verification steps and results
- Error conditions and exceptions
- Database updates 