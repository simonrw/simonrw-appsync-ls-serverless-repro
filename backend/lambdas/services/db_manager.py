import logging as log
from functools import wraps

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from lambdas.services import secrets_service
from lambdas.utils.common import Singleton, ServiceException


def get_db_url(secret: dict, db_name: str) -> str:
    return f"postgresql+psycopg2://{secret['username']}:{secret['password']}@" \
           f"{secret['host']}:{secret['port']}/{db_name}"


def get_app_db():
    return DbManager(connection_secret='db-app-secret', db_name='example')


# noinspection PyTypeChecker
class DbManager(metaclass=Singleton):  # pylint: disable=too-many-instance-attributes

    def __init__(self,  # pylint: disable=too-many-arguments
                 connection_secret,
                 db_name,
                 pool_pre_ping=True,
                 pool_recycle=300,
                 isolation_level=None,
                 debug=False):

        self.secret = secrets_service.get_secret_value(connection_secret, result_type=dict)
        self.db_name = db_name
        self.username = self.secret['username']
        self.pool_pre_ping = pool_pre_ping
        self.pool_recycle = pool_recycle
        self.isolation_level = isolation_level
        self.debug = debug
        self._engine = None
        self.session: Session = None

    def __enter__(self):
        if self._engine is None:
            self.__init_connection()

        session_object = sessionmaker(self._engine)
        self.session = session_object(bind=self._engine)
        return self

    def __exit__(self, *args, **kwargs):
        self.session.close()
        self.session = None

    def __init_connection(self):
        self._engine = create_engine(
            url=get_db_url(self.secret, self.db_name),
            echo=self.debug,
            future=True,
            pool_pre_ping=self.pool_pre_ping,
            pool_recycle=self.pool_recycle,
            isolation_level=self.isolation_level)

    def destroy(self):
        if self.session is not None:
            log.error("Open database session found! Will ROLLBACK !!!")
            self.session.rollback()
            self.session.close()
            self.session: Session = None

        self._engine = None
        DbManager._instances = {}


def with_db_session(fn):
    db_manager = get_app_db()

    @wraps(fn)
    def wrapper(*args, **kwargs):
        with db_manager as db:
            try:
                return fn(*args, **kwargs)
            except ServiceException as e:
                db.session.rollback()
                raise e
            except Exception as e:
                log.exception("Internal server error")
                db.session.rollback()
                raise ServiceException("Internal server error") from e
    return wrapper

