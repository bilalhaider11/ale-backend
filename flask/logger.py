import logging
import os
import sys

import rollbar
import rollbar.contrib.flask
from flask import got_request_exception
from rollbar.logger import RollbarHandler

from common.app_config import get_config

config = get_config()

config.ROLLBAR_ACCESS_TOKEN = None

if config.ROLLBAR_ACCESS_TOKEN:
    rollbar.init(
        access_token=config.ROLLBAR_ACCESS_TOKEN,
        environment=config.APP_ENV,
        root=os.path.dirname(os.path.realpath(__file__)),
        allow_logging_basic_config=False
    )


def _get_log_level():
    if config.APP_ENV != "production":
        return logging.DEBUG
    return getattr(logging, config.LOGLEVEL, 'INFO')


def _get_formatter():
    return logging.Formatter('%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s')


def rollbar_except_hook(exc_type, exc_value, traceback):
    # Report the issue to rollbar here.
    rollbar.report_exc_info((exc_type, exc_value, traceback))
    # display the error as normal here
    sys.__excepthook__(exc_type, exc_value, traceback)


def set_rollbar_exception_catch():
    sys.excepthook = rollbar_except_hook


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(_get_formatter())
    return console_handler


def get_rollbar_handler():
    loglevel = getattr(logging, config.LOGLEVEL, 'WARN')
    rollbar_handler = RollbarHandler(access_token=config.ROLLBAR_ACCESS_TOKEN, environment=config.APP_ENV)
    rollbar_handler.setLevel(loglevel)
    return rollbar_handler


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)

    logger.handlers.clear()

    logger.setLevel(_get_log_level())  # better to have too much log than not enough
    logger.addHandler(get_console_handler())

    if config.ROLLBAR_ACCESS_TOKEN:
        logger.addHandler(get_rollbar_handler())

    logger.propagate = False
    return logger


def set_request_exception_signal(app):
    got_request_exception.connect(rollbar.contrib.flask.report_exception, app)


logger = get_logger(__name__)
