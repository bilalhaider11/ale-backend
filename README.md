# ALE Backend

This repository contains the backend services for the **ALE Healthtech** system, including an API, message broker, database, and email processor.

---

## 🚀 Getting Started

<details>
<summary>Set up environment variables</summary>

1. Copy the example environment files:
   ```bash
   cp .env.secrets.example .env.secrets
   cp example.env <environment>.env  # e.g., local.env, dev.env, prod.env
   ```

2. Update the environment variables in your copied files. Keep the existing values except for AWS-specific and third-party service variables which need your actual credentials.

### Environment Variables Reference

#### General Configuration
- `APP_ENV` - Application environment (local, dev, prod)
- `LOG_LEVEL` - System log level (DEBUG, INFO, WARN, ERROR)
- `ROLLBAR_LEVEL` - Log level for Rollbar error tracking
- `DEBUG` - Enable debug mode (true/false)

#### Vue Frontend
- `VUE_APP_URI` - Frontend application URI

#### Database (PostgreSQL)
- `POSTGRES_HOST` - Database host
- `POSTGRES_PORT` - Database port
- `POSTGRES_USER` - Database username
- `POSTGRES_PASSWORD` - Database password (**update with your password**)
- `POSTGRES_DB` - Database name

#### Message Queue (RabbitMQ)
- `RABBITMQ_HOST` - RabbitMQ host
- `RABBITMQ_PORT` - RabbitMQ port
- `RABBITMQ_USER` - RabbitMQ username
- `RABBITMQ_PASSWORD` - RabbitMQ password (**update with your password**)
- `RABBITMQ_VIRTUAL_HOST` - RabbitMQ virtual host

#### Queue Configuration
- `QUEUE_NAME_PREFIX` - Prefix for all queue names
- Various `*_QUEUE_NAME` variables - Specific queue names for different processors

#### Email Service
- `EMAIL_PROVIDER` - Email provider (mailjet or ses)
- `MAILJET_API_KEY` - Mailjet API key (**add your key**)
- `MAILJET_API_SECRET` - Mailjet API secret (**add your secret**)

#### AWS Services
- `AWS_REGION` - AWS region
- `AWS_ACCESS_KEY_ID` - AWS access key (**add your key**)
- `AWS_ACCESS_KEY_SECRET` - AWS secret key (**add your secret**)
- `AWS_S3_BUCKET_NAME` - S3 bucket for uploads (**update with your bucket**)
- `AWS_S3_KEY_PREFIX` - S3 key prefix
- `AWS_S3_LOGOS_BUCKET_NAME` - S3 bucket for logos (**update with your bucket**)
- `BASE_DOMAIN` - Base domain for the application (**update with your domain**)
- `ROUTE53_HOSTED_ZONE_ID` - Route53 hosted zone ID for the base domain (**add your zone ID**)
- `CLOUDFRONT_DISTRIBUTION_DOMAIN` - CloudFront distribution domain for serving logos. For non-production environments, this can also be S3 bucket base URL. (**add your domain**)

#### Security & Authentication
- `SECRET_KEY` - Flask secret key (**update with secure random string**)
- `SECURITY_PASSWORD_SALT` - Password salt (**update with secure random string**)
- `AUTH_JWT_SECRET` - JWT secret key (**update with secure random string**)
- `ACCESS_TOKEN_EXPIRE` - Access token expiration time (seconds)
- `RESET_TOKEN_EXPIRE` - Password reset token expiration (seconds)
- `INVITATION_TOKEN_EXPIRE` - Invitation token expiration (seconds)

#### File Upload Service
- `FILESTACK_API_KEY` - Filestack API key (**add your key**)
- `FILESTACK_APP_SECRET` - Filestack app secret (**add your secret**)

#### Error Tracking
- `ROLLBAR_ACCESS_TOKEN` - Rollbar access token (**add your token**)

#### External Data Sources
- `OIG_WEBPAGE_URL` - OIG exclusions webpage URL
- `OIG_CSV_DOWNLOAD_URL` - OIG CSV download URL

</details>

<details>
<summary>OAuth Configuration</summary>

For setting up Google and Microsoft OAuth authentication, see the [OAuth Setup Guide](oauth.md).

</details>


### Running the system

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

**Description:** Service processes CSV files for current employees and current caregivers that are uploaded to S3 under the employees-list/ and caregivers-list/ prefixes. It automatically updates the employee table with the latest data, maintaining indexed fields to enable fast and efficient employee lookups.

---

### Patient Import

**Description:** Service processes CSV and XLSX files for patients that are uploaded to S3 under the patients-list/ prefix. It automatically updates the patient table with the latest data, maintaining indexed fields to enable fast and efficient patient lookups.

---

### OIG Update Check

**Description:** Daily cron service that monitors the OIG (Office of Inspector General) exclusions database for updates and automatically imports new data when available. Maintains the `oig_employees_exclusion` table with current exclusion records and tracks check status in `oig_exclusions_check` table.

### Exclusions Match Service

**Description:** Service that is triggered when a new employee is imported or added manually to find and insert an exclusion match record.



