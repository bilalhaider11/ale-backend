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

    @property
    def DEFAULT_USER_PASSWORD(self):
        import random, string
        if self.APP_ENV == "production":
            return ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        else:
            return 'Default@Password123'

def get_config() -> Config:
    conf = Config()
    return conf


config = get_config()
