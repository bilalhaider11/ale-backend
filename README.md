# ALE Backend

This repository contains the backend services for the **ALE Healthtech** system, including an API, message broker, database, and email processor.

---

## 🚀 Getting Started

To run the backend locally, use:

```bash
bash run.py
```

## 🧱 Services

### Postgres

**Description:** To be added

---

### RabbitMQ

**Description:** To be added

---

### API

**Description:** To be added

---

### Email Transmitter

**Description:** To be added

---

### Organization Processor

**Description:** Service that processes organization data changes, manages custom subdomains via Route53, and handles organization logo storage in S3.

---

### Employee Import

**Description:** Service processes CSV files for current employees and current caregivers that are uploaded to S3 under the employees-list/ and caregivers-list/ prefixes. It automatically updates the current_employee and current_caregiver tables with the latest data, maintaining indexed fields to enable fast and efficient employee lookups.

---

### OIG Update Check

**Description:** Daily cron service that monitors the OIG (Office of Inspector General) exclusions database for updates and automatically imports new data when available. Maintains the `oig_employees_exclusion` table with current exclusion records and tracks check status in `oig_exclusions_check` table.
