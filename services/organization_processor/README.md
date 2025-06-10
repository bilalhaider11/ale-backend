# Organization Processor Service

This service processes organization data changes, manages custom subdomains via Route53, and handles organization logo storage in S3.

## Features

- Transfers organization logo images to S3
- Creates/updates DNS CNAME entries in Route53 for organization subdomains
- Processes organization data changes

## Configuration

The service requires the following environment variables:

- `AWS_ACCESS_KEY_ID`: AWS access key with permissions for S3 and Route53
- `AWS_ACCESS_KEY_SECRET`: AWS secret key
- `AWS_REGION`: AWS region (e.g., us-east-1)
- `AWS_S3_BUCKET_NAME`: S3 bucket name for storing organization logos
- `AWS_S3_KEY_PREFIX`: Optional prefix for S3 keys
- `BASE_DOMAIN`: Base domain for organization subdomains (e.g., alehealthtech.com)
- `SUBDOMAIN_TARGET`: Target domain for CNAME records (e.g., CloudFront distribution domain)

## Message Format

The service expects messages in the following format:

```json
{
  "organization_id": "org-uuid",
  "action": "create|update|delete",
  "data": {
    // Optional additional organization data
  }
}
```

## Development

To run the service locally:

1. Set up the required environment variables
2. Run the service using Docker:

```bash
docker build -t organization-processor -f services/organization_processor/Dockerfile .
docker run -it --env-file .env organization-processor
```
# Organization Processor Service
This service processes organization updates from SQS messages.

## Features
- Processes organization updates
- Handles logo transfers to S3
- Creates CNAME records in Route53 for subdomains

## Development
Poetry is used for dependency management for python packages.
1. To add new package, goto [organization_processor](./) folder and run

    ```
   poetry add PACKAGE_NAME
    ```

2. Increase the app version using
    ```
    poetry version patch | minor | major 
   ```
   **Note:** Use `patch` for patch version increase, `minor` for minor version increase or `major` for major version increase.


3. Update all dependencies using
    ```
   poetry update
   ```
   Update specific libraries using
    ```
   poetry update libraryName1 libraryName2
   ```
