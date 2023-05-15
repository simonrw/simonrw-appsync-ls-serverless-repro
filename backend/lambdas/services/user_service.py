from functools import wraps

from lambdas import is_local
from lambdas.dao import user_dao
from lambdas.models import UserAccount
from lambdas.services.db_manager import get_app_db
from lambdas.utils.common import ServiceException, RequestException

import logging as log

db = get_app_db()


def get_user_info(user_name) -> dict:
    user = user_dao.find_user(user_name)
    if user is not None:
        return user.to_dict()
    raise ServiceException("Bad Request")


def create_or_update_user(user_name: str, user_attributes: dict):
    user = user_dao.find_user(user_name)
    name = _get_name(user_attributes)
    email = user_attributes["email"]
    if user is None:
        user = UserAccount(
            user_name=user_name, name=name, email=email,
        )
        db.session.add(user)
    else:
        user.name = name
        user.email = email

    db.session.commit()


def delete_user(user_name: str):
    user = user_dao.find_user(user_name)
    log.debug(user_name)
    log.debug(user)
    if user is not None:
        db.session.delete(user)
        db.session.commit()
    else:
        raise RequestException("User not found")


def _get_name(user_attributes):
    name = user_attributes.get("name")
    if name is None:
        name = f"{user_attributes.get('family_name', '')} {user_attributes.get('given_name', '')}"
    return name


def authorize_user(get_user_as_kwarg: bool = False):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            event = args[0]
            user_name = event.get("identity", {}).get("username", None)
            if user_name is None:
                if is_local():
                    log.warning(
                        "!!! RUNNING ON LOCAL PROFILE UTILIZING HARDCODED USERNAME !!!"
                    )
                    user_name = "testuser"
                else:
                    raise ServiceException("Unauthorized")

            user = user_dao.find_user(user_name)
            if user is None:
                raise ServiceException("Unauthorized")

            if get_user_as_kwarg is True:
                kwargs["user"] = user

            return fn(*args, **kwargs)

        return wrapper

    return decorator
