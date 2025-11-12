import os
from typing import Type

from pydantic import Field
from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):    
    APP_ENV: str

    # Sets the flask ENV
    @property
    def ENV(self):
        return self.APP_ENV

class Config(BaseConfig):
    DEBUG: bool = Field(default=False)
    TESTING: bool = Field(default=False)
    LOG_LEVEL: str = Field(default='INFO')
    ROLLBAR_LEVEL: str = Field(default='WARN')

    ACCESS_TOKEN_EXPIRE: int = Field(default=518400)
    RESET_TOKEN_EXPIRE: int = Field(default=60*60*24*3)  # 3 days
    INVITATION_TOKEN_EXPIRE: int = Field(default=60*60*24*3)

    MIME_TYPE: str = 'application/json'

    SECRET_KEY: str = Field(default=None)
    SECURITY_PASSWORD_SALT: str = Field(default=None)

    VUE_APP_URI: str = Field(default=None)

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_VIRTUAL_HOST: str = Field(default='/')
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str

    AUTH_JWT_SECRET: str

    ROLLBAR_ACCESS_TOKEN: str = Field(default=None)

    QUEUE_NAME_PREFIX: str = Field(default='')
    EMAIL_SERVICE_PROCESSOR_QUEUE_NAME: str = Field(alias='EmailServiceProcessor_QUEUE_NAME', default='email-transmitter')
    FILE_PROCESSOR_QUEUE_NAME: str = Field(alias='FileProcessor_QUEUE_NAME', default='file-processor')
    DOCUMENT_ANALYSIS_RESPONSE_TOPIC_NAME: str = Field(default="document-analysis-response")
    ORGANIZATION_PROCESSOR_QUEUE_NAME: str = Field(alias='OrganizationProcessor_QUEUE_NAME', default='organization-processor')
    EMPLOYEE_IMPORT_PROCESSOR_QUEUE_NAME: str = Field(alias='EmployeeImportProcessor_QUEUE_NAME', default='employee-import')
    EMPLOYEE_EXCLUSION_MATCH_PROCESSOR_QUEUE_NAME: str = Field(alias='EmployeeExclusionMatchProcessor_QUEUE_NAME', default='employee-exclusion-match-processor')
    OIG_VERIFIER_PROCESSOR_QUEUE_NAME: str = Field(alias='OigVerifierProcessor_QUEUE_NAME', default='oig-verifier')
    PATIENT_IMPORT_PROCESSOR_QUEUE_NAME: str = Field(alias='PatientImportProcessor_QUEUE_NAME', default='patient-import')
    ALERT_PROCESSOR_QUEUE_NAME: str = Field(alias='AlertProcessor_QUEUE_NAME', default='alert-processor')

    BASE_DOMAIN: str = Field(default=None)
    ROUTE53_HOSTED_ZONE_ID: str = Field(default=None)
    CLOUDFRONT_DISTRIBUTION_DOMAIN: str = Field(default=None)
    AWS_S3_LOGOS_BUCKET_NAME: str

    AWS_ACCESS_KEY_ID: str
    AWS_ACCESS_KEY_SECRET: str
    AWS_REGION: str = Field(default="us-west-2")
    AWS_S3_BUCKET_NAME: str
    AWS_S3_KEY_PREFIX: str = Field(default="")

    FILESTACK_API_KEY: str
    FILESTACK_APP_SECRET: str

    OIG_WEBPAGE_URL: str = Field(default="")
    OIG_CSV_DOWNLOAD_URL: str = Field(default="")

    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")

    MICROSOFT_CLIENT_ID: str = Field(default="")
    MICROSOFT_CLIENT_SECRET: str = Field(default="")

    # Pusher configuration
    PUSHER_APP_ID: str = Field(default="")
    PUSHER_KEY: str = Field(default="")
    PUSHER_SECRET: str = Field(default="")
    PUSHER_CLUSTER: str = Field(default="us2")

    @property
    def DEFAULT_USER_PASSWORD(self):
        import random, string
        if self.APP_ENV == "production":
            return 'P!'.join(random.choices(string.ascii_letters + string.digits, k=12))
        else:
            return 'Default@Password123'

    @property
    def PREFIXED_DOCUMENT_ANALYSIS_RESPONSE_TOPIC_NAME(self):
        if self.QUEUE_NAME_PREFIX:
            return f"{self.QUEUE_NAME_PREFIX}{self.DOCUMENT_ANALYSIS_RESPONSE_TOPIC_NAME}"
        return self.DOCUMENT_ANALYSIS_RESPONSE_TOPIC_NAME

    @property
    def PREFIXED_FILE_PROCESSOR_QUEUE_NAME(self):
        if self.QUEUE_NAME_PREFIX:
            return f"{self.QUEUE_NAME_PREFIX}{self.FILE_PROCESSOR_QUEUE_NAME}"
        return self.FILE_PROCESSOR_QUEUE_NAME
        
    @property
    def PREFIXED_ORGANIZATION_PROCESSOR_QUEUE_NAME(self):
        if self.QUEUE_NAME_PREFIX:
            return f"{self.QUEUE_NAME_PREFIX}{self.ORGANIZATION_PROCESSOR_QUEUE_NAME}"
        return self.ORGANIZATION_PROCESSOR_QUEUE_NAME
        
    @property
    def PREFIXED_EMPLOYEE_IMPORT_PROCESSOR_QUEUE_NAME(self):
        if self.QUEUE_NAME_PREFIX:
            return f"{self.QUEUE_NAME_PREFIX}{self.EMPLOYEE_IMPORT_PROCESSOR_QUEUE_NAME}"
        return self.EMPLOYEE_IMPORT_PROCESSOR_QUEUE_NAME

    @property
    def PREFIXED_EMPLOYEE_EXCLUSION_MATCH_PROCESSOR_QUEUE_NAME(self):
        if self.QUEUE_NAME_PREFIX:
            return f"{self.QUEUE_NAME_PREFIX}{self.EMPLOYEE_EXCLUSION_MATCH_PROCESSOR_QUEUE_NAME}"
        return self.EMPLOYEE_EXCLUSION_MATCH_PROCESSOR_QUEUE_NAME
    
    @property
    def PREFIXED_OIG_VERIFIER_QUEUE_NAME(self):
        if self.QUEUE_NAME_PREFIX:
            return f"{self.QUEUE_NAME_PREFIX}{self.OIG_VERIFIER_PROCESSOR_QUEUE_NAME}"
        return self.OIG_VERIFIER_PROCESSOR_QUEUE_NAME
    
    @property
    def PREFIXED_PATIENT_IMPORT_PROCESSOR_QUEUE_NAME(self):
        if self.QUEUE_NAME_PREFIX:
            return f"{self.QUEUE_NAME_PREFIX}{self.PATIENT_IMPORT_PROCESSOR_QUEUE_NAME}"
        return self.PATIENT_IMPORT_PROCESSOR_QUEUE_NAME
        
    @property
    def PREFIXED_ALERT_PROCESSOR_QUEUE_NAME(self):
        if self.QUEUE_NAME_PREFIX:
            return f"{self.QUEUE_NAME_PREFIX}{self.ALERT_PROCESSOR_QUEUE_NAME}"
        return self.ALERT_PROCESSOR_QUEUE_NAME

def get_config() -> Config:
    conf = Config()
    return conf


config = get_config()
