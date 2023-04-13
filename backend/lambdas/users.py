from lambdas import init_lambda
from lambdas.models import UserAccount
from lambdas.services import user_service
from lambdas.services.db_manager import with_db_session
from lambdas.services.user_service import authorize_user
from lambdas.utils.common import ServiceException

init_lambda()


@with_db_session
@authorize_user(get_user_as_kwarg=True)
def handler(event, _context, user: UserAccount):
    request = event.get('info', {}).get('fieldName')
    if request == 'user':
        return user.to_dict()
    if request == 'getUser':
        user_name = event['arguments']['userName']
        return user_service.get_user_info(user_name)
    raise ServiceException(f"Unknown request: '{request}')")
