from lambdas.models import UserAccount
from lambdas.services.db_manager import get_app_db

db = get_app_db()


def find_user(user_name) -> UserAccount:
    return db.session.query(UserAccount)\
        .filter(UserAccount.user_name == user_name)\
        .one_or_none()
