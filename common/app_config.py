import os
from typing import Type

from pydantic import Field
from pydantic_settings import BaseSettings
from werkzeug.utils import import_string


class BaseConfig(BaseSettings):
    APP_ENV: str = Field(env='APP_ENV')

    # Sets the flask ENV
    @property
    def ENV(self):
        return self.APP_ENV


class Config(BaseConfig):
    DEBUG: bool = Field(env='DEBUG', default=False)
    TESTING: bool = Field(env='TESTING', default=False)
    LOGLEVEL: str = Field(env='LOGLEVEL', default='INFO')

    ACCESS_TOKEN_EXPIRE: int = Field(env='ACCESS_TOKEN_EXPIRE', default=3600)
    RESET_TOKEN_EXPIRE: int = Field(env='ACCESS_TOKEN_EXPIRE', default=60*60*24*3)  # 3 days
    INVITATION_TOKEN_EXPIRE: int = Field(env='INVITATION_TOKEN_EXPIRE', default=60*60*24*3)

    MIME_TYPE: str = 'application/json'

    SECRET_KEY: str = Field(env='SECRET_KEY', default=None)
    SECURITY_PASSWORD_SALT: str = Field(env='SECURITY_PASSWORD_SALT', default=None)

    VUE_APP_URI: str = Field(env='VUE_APP_URI', default=None)

    POSTGRES_HOST: str = Field(env='POSTGRES_HOST')
    POSTGRES_PORT: int = Field(env='POSTGRES_PORT')
    POSTGRES_USER: str = Field(env='POSTGRES_USER')
    POSTGRES_PASSWORD: str = Field(env='POSTGRES_PASSWORD')
    POSTGRES_DB: str = Field(env='POSTGRES_DB')

    RABBITMQ_HOST: str = Field(env='RABBITMQ_HOST')
    RABBITMQ_PORT: int = Field(env='RABBITMQ_PORT')
    RABBITMQ_VIRTUAL_HOST: str = Field(env='RABBITMQ_VIRTUAL_HOST', default='/')
    RABBITMQ_USER: str = Field(env='RABBITMQ_USER')
    RABBITMQ_PASSWORD: str = Field(env='RABBITMQ_PASSWORD')

    AUTH_JWT_SECRET: str = Field(env='AUTH_JWT_SECRET')

    ROLLBAR_ACCESS_TOKEN: str = Field(env='ROLLBAR_ACCESS_TOKEN', default=None)

    QUEUE_NAME_PREFIX: str = Field(env='QUEUE_NAME_PREFIX', default='')
    EMAIL_SERVICE_PROCESSOR_QUEUE_NAME: str = Field(env='EmailServiceProcessor_QUEUE_NAME', default='email-transmitter')
    FILE_PROCESSOR_QUEUE_NAME: str = Field(env='FileProcessor_QUEUE_NAME', default='file-processor')
    DOCUMENT_ANALYSIS_RESPONSE_TOPIC_NAME: str = Field(env='DOCUMENT_ANALYSIS_RESPONSE_TOPIC_NAME', default="document-analysis-response")
    ORGANIZATION_PROCESSOR_QUEUE_NAME: str = Field(env='OrganizationProcessor_QUEUE_NAME', default='organization-processor')
    
    BASE_DOMAIN: str = Field(env='BASE_DOMAIN', default=None)
    ROUTE53_HOSTED_ZONE_ID: str = Field(env='ROUTE53_HOSTED_ZONE_ID', default=None)
    CLOUDFRONT_DISTRIBUTION_DOMAIN: str = Field(env='CLOUDFRONT_DISTRIBUTION_DOMAIN', default=None)
    AWS_S3_LOGOS_BUCKET_NAME: str = Field(env="AWS_S3_LOGOS_BUCKET_NAME")

    AWS_ACCESS_KEY_ID: str = Field(env="AWS_ACCESS_KEY_ID")
    AWS_ACCESS_KEY_SECRET: str = Field(env="AWS_ACCESS_KEY_SECRET")
    AWS_REGION: str = Field(env="AWS_REGION", default="us-west-2")
    AWS_S3_BUCKET_NAME: str = Field(env="AWS_S3_BUCKET_NAME")
    AWS_S3_KEY_PREFIX: str = Field(env="AWS_S3_KEY_PREFIX", default="")

    FILESTACK_API_KEY: str = Field(env="FILESTACK_API_KEY")
    FILESTACK_APP_SECRET: str = Field(env="FILESTACK_APP_SECRET")

    OIG_WEBPAGE_URL: str = Field(env="OIG_WEBPAGE_URL", default="")
    OIG_CSV_DOWNLOAD_URL: str = Field(env="OIG_CSV_DOWNLOAD_URL", default="")

    @property
    def DEFAULT_USER_PASSWORD(self):
        import random, string
        if self.APP_ENV == "production":
            return ''.join(random.choices(string.ascii_letters + string.digits, k=12))
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


def get_config() -> Config:
    conf = Config()
    return conf


config = get_config()
