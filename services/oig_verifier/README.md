# OIG Verifier Service

This service processes exclusion matches and performs verification tasks when matches are found between employees/caregivers and the OIG exclusion list.

## Purpose

The service receives messages via RabbitMQ when exclusion matches are found and performs the following operations:
1. Receives match data from the employee exclusion match service
2. Performs verification tasks (custom business logic)
3. Updates match status and adds verification results
4. Triggers notifications or other actions as needed

## Dependencies

- RabbitMQ for message processing
- PostgreSQL database with the following tables:
  - `employee_exclusion_match`
  - `employee`
  - `oig_employees_exclusion`

## Usage

The service runs as a Docker container and processes messages automatically when they are received from the configured RabbitMQ queue.

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
      "match_type": "name_and_dob"
    }
  ]
}
``` 