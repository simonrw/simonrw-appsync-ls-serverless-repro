from gql.dsl import DSLSchema, DSLMutation, DSLInlineFragment, DSLMetaField
from random_username.generate import generate_username

from aws_utils import create_user, GROUP_SYSADMIN, get_gql_client, query_gql, AWSUtils
from conftest import TestContext
from utils import str_utils
from utils.common import Singleton


class PortalUtils(metaclass=Singleton):
    def __init__(self, ctx: TestContext):
        self.ctx = ctx
        self.aws = AWSUtils(ctx)
        self.sysadmin = create_user(ctx=ctx, groups=[GROUP_SYSADMIN], do_auth=False)

    def authenticate_sysadmin(self):
        self.sysadmin = self.aws.authenticate(self.sysadmin)


def create_org(ctx):
    org_name = generate_username()[0]
    utils = PortalUtils(ctx=ctx)
    utils.authenticate_sysadmin()
    client = get_gql_client(ctx=ctx, user=utils.sysadmin)
    ds: DSLSchema = DSLSchema(client.schema)
    query = DSLMutation(
        ds.Mutation.createOrganisation.args(
            name=org_name,
            displayName=org_name,
            rootName=org_name
        ).select(
            ds.Organisation.id,
            ds.Organisation.name,
            ds.Organisation.displayName,
            ds.Organisation.rootName,
           )
       )
    result = query_gql(client=client, query=query)
    organisation = result['createOrganisation']
    org_uuid = str_utils.get_uuid(organisation['id'])
    assert org_uuid is not None
    assert organisation['name'] == org_name
    assert organisation['displayName'] == org_name
    assert organisation['rootName'] == org_name

    return organisation


def ticket_sla_select(ds: DSLSchema):
    frag = DSLInlineFragment()
    frag.on(ds.TicketSLAReport)
    frag.select(ds.TicketSLAReport.items.select(
        ds.TicketSLA.key,
        ds.TicketSLA.summary,
        ds.TicketSLA.priority,
        ds.TicketSLA.status,
        ds.TicketSLA.createdDate,
        ds.TicketSLA.resolutionDate,
        ds.TicketSLA.type,
        ds.TicketSLA.reactionSeconds,
        ds.TicketSLA.reactionBreached,
        ds.TicketSLA.resolutionSeconds,
        ds.TicketSLA.resolutionBreached,
        ds.TicketSLA.comment,
        ds.TicketSLA.excludeSLA,
        ds.TicketSLA.serviceDeskUrl
    ))

    return [DSLMetaField("__typename"),
            ds.SLAReport.id,
            ds.SLAReport.name,
            ds.SLAReport.created,
            ds.SLAReport.status,
            ds.SLAReport.startDate,
            ds.SLAReport.endDate,
            frag]


def uptime_sla_select(ds: DSLSchema):
    frag = DSLInlineFragment()
    frag.on(ds.UptimeSLAReport)
    frag.select(ds.UptimeSLAReport.items.select(
        ds.ServiceUptime.name,
        ds.ServiceUptime.serviceActivated,
        ds.ServiceUptime.outages.select(
            ds.ServiceOutage.startTimestamp,
            ds.ServiceOutage.endTimestamp
        ),
        ds.ServiceUptime.monitoringOutages.select(
            ds.MonitoringOutage.startDate,
            ds.MonitoringOutage.endDate,
            ds.MonitoringOutage.durationSeconds
        ),
        ds.ServiceUptime.responseTimeMin,
        ds.ServiceUptime.responseTimeAvg,
        ds.ServiceUptime.responseTimeMax,
        ds.ServiceUptime.expectedSamples,
        ds.ServiceUptime.sampleCount,
        ds.ServiceUptime.scheduleIntervalMinutes
    ))

    return [DSLMetaField("__typename"),
            ds.SLAReport.id,
            ds.SLAReport.name,
            ds.SLAReport.created,
            ds.SLAReport.status,
            ds.SLAReport.startDate,
            ds.SLAReport.endDate,
            frag]
