import json
import logging
import os

from aws_xray_sdk.core import patch_all

from lambdas.utils.common import LogManager, init_json_serialisation

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
AWS_REGION = os.environ.get('AWS_REGION', None)
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'DEV').upper()


def init_lambda():
    if LOG_LEVEL == 'DEBUG':
        print("WARNING!!! Setting log level to DEBUG!!!")
        log_level = logging.DEBUG
    elif LOG_LEVEL == 'INFO':
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    log_manager = LogManager()
    log_manager.init_logging(log_level=log_level)

    init_json_serialisation()

    if AWS_REGION is not None:
        patch_all()


def is_dev():
    return ENVIRONMENT == 'DEV' or is_local()


def is_local():
    return ENVIRONMENT == 'LOCAL'


def get_mock_data(path: str) -> dict:
    with open(file=path, mode='r', encoding='utf8') as file:
        return json.load(file)
