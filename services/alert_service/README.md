# Alert Service

This service processes messages to create and manage organizational alerts.

## Purpose

The service receives messages via RabbitMQ and performs the following operations:
1. Creates new alerts for organizations
2. Updates alert status
3. Manages which users have read alerts

## Alert Levels
- 0: Info
- 1: Warning
- 2: Critical

## Alert Status
- 0: Open
- 1: In Progress
- 2: Addressed

## Dependencies

- RabbitMQ for message processing
- PostgreSQL database with the following tables:
  - `alert`
  - `alert_person`

## Usage

The service runs as a Docker container and processes messages automatically when they are received from the configured RabbitMQ queue.
