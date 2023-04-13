import decimal
import logging as log
import sys
from datetime import datetime, date
from enum import Enum
from functools import wraps
from json import JSONEncoder
from typing import Callable
from uuid import UUID

from utils import dt_utils


def serialize_object(value, default: Callable = None, **kwargs):  # pylint:disable=too-many-return-statements
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return dt_utils.timestamp_to_iso(value)
    if isinstance(value, date):
        return dt_utils.date_to_iso(value)
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, decimal.Decimal):
        return float(value)
    if default is not None:
        self = kwargs.get('self', None)
        if self is not None:
            return default(self, value)
        return default(value)
    return str(value)


def init_json_serialisation():
    default = JSONEncoder.default

    def custom_serializer(self, obj):
        return serialize_object(value=obj, default=default, self=self)

    JSONEncoder.default = custom_serializer


def mask_log_values(parameters: dict):
    if parameters is not None:
        log_manager = LogManager()
        for value in parameters.values():
            log_manager.add_mask_value(value)


def unmask_log_values(parameters: dict):
    if parameters is not None:
        log_manager = LogManager()
        for value in parameters.values():
            log_manager.remove_mask_value(value)


class ServiceException(Exception):
    pass


class RequestException(Exception):
    pass


class SensitiveLogFormatter(log.Formatter):

    def __init__(self, formatter, mask_values):
        super().__init__()
        self.formatter = formatter
        if mask_values:
            self.mask_values = mask_values
        else:
            self.mask_values = []

    def _filter(self, value: str):
        if value and isinstance(value, str):
            for mask_value in self.mask_values:
                value = value.replace(str(mask_value), '*****')
        return value

    def format(self, record):
        if record:
            original = self.formatter.format(record)
            return self._filter(original)
        return None


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class LogManager(metaclass=Singleton):

    def __init__(self):
        self.handler = None
        self.mask_values = []
        self.formatter = None

    def init_logging(self, mask_values: list = None, log_level=log.INFO, stream=None):
        if stream is None:
            stream = sys.stdout

        root = log.getLogger()
        if self.handler is not None:
            root.removeHandler(self.handler)

        self.handler = log.StreamHandler(stream)
        formatter = log.Formatter('%(asctime)s %(levelname)s (%(filename)s:%(lineno)d) - %(message)s')
        self.handler.setFormatter(formatter)
        root.addHandler(self.handler)

        self.mask_values = []
        if mask_values is not None:
            for value in mask_values:
                self.mask_values.append(str(value))

            self.mask_values.sort(key=len, reverse=True)

        self.formatter = SensitiveLogFormatter(self.handler.formatter, self.mask_values)
        for handler in log.root.handlers:
            handler.setFormatter(self.formatter)

        LogManager.set_log_level(log_level=log_level)

    @staticmethod
    def get_log_level_name():
        return log.getLevelName(log.getLogger().level)

    @staticmethod
    def set_log_level(log_level=log.INFO):
        root = log.getLogger()
        root.setLevel(log_level)
        for handler in log.root.handlers:
            handler.setLevel(log_level)

    @staticmethod
    def set_debug(debug=False):
        if debug is True:
            root = log.getLogger()
            log_level = root.level
            if log_level != log.DEBUG:
                LogManager.set_log_level(log.DEBUG)

    def add_mask_value(self, mask_value):
        value = str(mask_value)
        if value not in self.mask_values:
            self.mask_values.append(value)
            self.mask_values.sort(key=len, reverse=True)
            if self.formatter is not None:
                self.formatter.mask_values = self.mask_values

    def remove_mask_value(self, mask_value):
        value = str(mask_value)
        if value in self.mask_values:
            self.mask_values.remove(value)
            self.mask_values.sort(key=len, reverse=True)
            if self.formatter is not None:
                self.formatter.mask_values = self.mask_values

    def destroy(self):
        self.mask_values = None
        self.formatter = None
        root = log.getLogger()
        root.removeHandler(self.handler)
        for handler in log.root.handlers:
            handler.setFormatter(None)
        log.shutdown()
        LogManager._instances = {}


def lambda_result(success: bool = False, message: str = None):
    result = {'success': success}
    if message is not None:
        result['message'] = message
    return result


def success_result(message: str = None):
    return lambda_result(success=True, message=message)


def build_result(result_field_name: str, response):
    result = success_result()
    result[result_field_name] = response
    return result


def build_error_result(message: str, exception: Exception = None):
    if exception is not None:
        log.error(message, exc_info=exception)
    return {"success": False, "errors": [message]}


def build_errors_result(message: str, errors: list = None):
    messages = []
    if errors is not None:
        for e in errors:
            messages.append(f"{e}")
    messages.append(message)
    return {"success": False, "errors": messages}


def build_result_from_dict(result_dict: dict):
    return success_result() | result_dict


def get_boolean(value: str) -> bool:
    if value is True or value in ('true', 'True'):
        return True
    return False


def handle_errors(db_session=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                log.exception("Internal server error")
                if db_session:
                    db_session.rollback()
                raise ServiceException("Internal server error") from e
        return wrapper
    return decorator


def get_field_value_or_raise(values: dict, field_name: str, message: str, result_type=None):
    return get_field_value(values, field_name, message=message, raise_exception=True, result_type=result_type)


def get_field_value(values: dict, field_name: str, message: str = None, raise_exception: bool = True, result_type=None):
    value = values.get(field_name, None)
    if value is None:
        if raise_exception:
            raise RequestException(message)
        return None

    if result_type is not None:
        if not isinstance(value, result_type):
            raise RequestException(f"Unexpected value type '{type(value)}' Should be {result_type}")

    return value


def list_to_dict(items: list, show: list[str] = None):
    result = []
    for item in items:
        result.append(item.to_dict(show=show))
    return result
