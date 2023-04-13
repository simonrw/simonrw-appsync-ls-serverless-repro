import logging
import os

import pytest

from lambdas.utils.common import LogManager


@pytest.fixture(scope="session", autouse=True)
def setup_unit_test():
    os.environ['DB_APP_SECRET'] = """{\"dbClusterIdentifier\":\"local-db-cluster\",
        \"password\":\"example\",
        \"dbname\":\"example\",
        \"engine\":\"postgres\",
        \"port\":5432,
        \"host\":\"localhost\",
        \"username\":\"example\"}"""

    log_manager = LogManager()
    log_manager.init_logging(log_level=logging.DEBUG)



