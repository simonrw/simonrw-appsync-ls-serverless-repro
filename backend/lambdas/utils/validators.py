
class ValidationException(Exception):
    pass


def is_defined(value):
    if value is None:
        return False

    value_type = type(value)
    if value_type == str:
        if value.strip() == '':
            return False
    elif value_type in (list, dict):
        if value is None or len(value) <= 0:
            return False
    return True


def get_event_value(event: dict, field: str, allowed_values: list = None, required: bool = True):
    value = event.get(field, None)
    if required is True and value is None:
        raise ValidationException(f"Field '{field}' is required")

    if allowed_values is not None and value not in allowed_values:
        raise ValidationException(f"Field '{field}' value {value} is not one of {allowed_values}")

    return value


def raise_not_defined(field_name: str, value):
    if not is_defined(value):
        raise ValidationException(f"{field_name} is not defined")


def raise_shorter_than(field_name: str, value, length: int = 3):
    raise_not_defined(field_name, value)
    if len(value) < length:
        raise ValidationException(f"{field_name} value too short")
