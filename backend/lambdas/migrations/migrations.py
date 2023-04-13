import logging as log

from alembic import command
from alembic.config import Config

from lambdas import init_lambda

init_lambda()


def handler(*_):
    try:
        log.info("Migrating the database schema")

        alembic_cfg = Config("lambdas/migrations/alembic.ini")
        command.upgrade(alembic_cfg, "head")
        return {'success': True, 'message': 'OK'}

    except Exception:  # pylint: disable=broad-except
        message = "Running database migration failed"
        log.exception(message)
        return {'success': False, 'message': message}


if __name__ == '__main__':
    handler(None, None)
