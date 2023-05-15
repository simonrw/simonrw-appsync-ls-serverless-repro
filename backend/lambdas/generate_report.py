import logging as log
import os
from uuid import uuid4

from gql import Client
from gql.dsl import DSLSchema, DSLMutation
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.appsync_auth import AppSyncIAMAuthentication

from lambdas import init_lambda
from utils.gql_utils import query_gql, get_graphql_schema

init_lambda()

if "LOCALSTACK_HOSTNAME" in os.environ:
    HOST = os.environ['LOCALSTACK_HOSTNAME']
    postfix = os.environ['GRAPHQL_ENDPOINT'].split('/graphql/')[-1].strip()
    GRAPHQL_ENDPOINT = f"{os.environ['AWS_ENDPOINT_URL']}/graphql/{postfix}"
else:
    GRAPHQL_ENDPOINT = os.environ['GRAPHQL_ENDPOINT']
    HOST = host = GRAPHQL_ENDPOINT.split('/')[2]


log.info("GRAPHQL_ENDPOINT %s", GRAPHQL_ENDPOINT)

GRAPHQL_ENDPOINT = GRAPHQL_ENDPOINT.strip()
SCHEMA = get_graphql_schema()


def handler(event, _context):
    log.info("Received event: %s", event)
    log.info("GRAPHQL_ENDPOINT %s", GRAPHQL_ENDPOINT)

    log.info("ENVIRONMENT %s", os.environ)

    # Generating the report out of the event data
    report_id = uuid4()
    auth = AppSyncIAMAuthentication(host=HOST)
    transport = AIOHTTPTransport(url=GRAPHQL_ENDPOINT, auth=auth)
    client = Client(transport=transport, fetch_schema_from_transport=False, schema=SCHEMA)
    trace_id = event['arguments']['traceId']
    ds: DSLSchema = DSLSchema(client.schema)
    query = DSLMutation(
        ds.Mutation.reportStatus()
        .args(traceId=trace_id,
              message="Report generated",
              id=str(report_id))
        .select(
            ds.SubscriptionResult.traceId,
            ds.SubscriptionResult.message,
            ds.SubscriptionResult.id))
    result = query_gql(client=client, query=query)

    return {'message': result['reportStatus']['message']}
