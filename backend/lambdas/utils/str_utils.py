import json
from typing import Optional, Any
from uuid import UUID


def get_bool(value: str, throw: bool = False) -> Optional[bool]:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    v = value.lower()
    if v in ['y', 'yes', 't', 'true', 'on', '1', 1]:
        return True
    if v in ['n', 'no', 'f', 'false', 'off', '0', 0]:
        return False

    if throw:
        raise ValueError(f"'{value}' is not a boolean")
    return None


def get_int(value, throw: bool = False) -> Optional[int]:
    if value is None:
        return None

    if isinstance(value, int):
        return value

    try:
        return int(value)
    except ValueError as e:
        if throw:
            raise e
        return None


def get_json(value: str, throw: bool = True) -> Optional[int]:
    if value is None:
        return None

    try:
        return json.loads(value)
    except ValueError as e:
        if throw:
            raise e
        return None


def parse_to_type(value: str) -> Any:
    result = get_int(value)
    if result is not None:
        return result

    result = get_bool(value)
    if result is not None:
        return result

    return value


def get_uuid(value):
    if value:
        if isinstance(value, UUID):
            return value
        return UUID(value)
    return None


def convert_snake_to_camel_case(value: str) -> str:
    components = value.split('_')
    return f"{components[0]}{''.join(x.title() for x in components[1:])}"
