import logging as log
from uuid import uuid4

from gql.dsl import DSLSchema, DSLMutation

import portal_utils
from tests.integration.aws_utils import create_user, get_gql_client, query_gql, GROUP_SYSADMIN

def test_generate_billing_report(ctx):

    log.info("GRAPHQL_URL: %s", ctx.graphql_url)

    sysadmin = create_user(ctx=ctx, groups=[GROUP_SYSADMIN])
    client = get_gql_client(ctx=ctx, user=sysadmin)
    ds: DSLSchema = DSLSchema(client.schema)
    trace_id = uuid4()
    query = DSLMutation(
        ds.Mutation.generateReport.args(
            traceId=str(trace_id),
            organisationId="saldkmadlknakjsndasd",
            reportName="Test Billing Report",
            month=1,
            year=2023)
        .select(
            ds.Result.message
        )
    )
    result = query_gql(client=client, query=query)
    assert result['generateBillingReport']['message'] == "Started"
