import logging as log
from dataclasses import dataclass

import boto3
import pytest

from lambdas.utils.common import LogManager, init_json_serialisation


@dataclass
class TestContext:
    region: str
    endpoint_url: str
    graphql_url: str
    host: str


def get_graphql_url(api_list_response: dict):
    api_list = api_list_response['graphqlApis']
    for api in api_list:
        if api['name'] == 'example-local-graphql':
            return api['uris']['GRAPHQL']

    raise Exception("Portal GraphQL API endpoint not found")


@pytest.fixture(scope="session", autouse=True)
def ctx():
    # os.environ['DB_APP_SECRET'] = """{\"dbClusterIdentifier\":\"local-db-cluster\",
    #     \"password\":\"example\",
    #     \"dbname\":\"example\",
    #     \"engine\":\"postgres\",
    #     \"port\":5432,
    #     \"host\":\"localhost\",
    #     \"username\":\"example\"}"""

    log_manager = LogManager()
    log_manager.init_logging(log_level=log.DEBUG)

    init_json_serialisation()

    endpoint_url = "http://localhost:4566"
    region = "us-east-1"
    session = boto3.Session(profile_name="serverless")
    client = session.client("appsync", endpoint_url=endpoint_url, region_name=region)

    url = get_graphql_url(client.list_graphql_apis())
    if not (url.startswith('http://') or url.startswith('https://')):
        raise Exception(f"Invalid URL {url}")

    host = url.split('/')[2]

    return TestContext(
        region=region,
        endpoint_url=endpoint_url,
        graphql_url=url,
        host=host
    )
