import json
import logging as log
import os
from dataclasses import dataclass
from uuid import uuid4

import boto3
from gql import gql, Client
from gql.dsl import dsl_gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.appsync_auth import AppSyncJWTAuthentication
from gql.transport.exceptions import TransportQueryError
from random_username.generate import generate_username

from tests.integration.conftest import TestContext
from utils.common import Singleton

GROUP_SYSADMIN: str = 'LOCAL_SYSADMIN'

ALL_GROUPS: list[str] = [GROUP_SYSADMIN]


@dataclass
class User:
    username: str
    password: str
    user_pool_id: str
    client_id: str
    token: str = None


class AWSUtils(metaclass=Singleton):

    def __init__(self, ctx: TestContext):
        self.ctx = ctx
        self.session = boto3.Session(profile_name="serverless")
        self.lambda_client = self.session.client(
            "lambda",
            endpoint_url=ctx.endpoint_url,
            region_name=ctx.region
        )
        self.cognito_client = self.session.client(
            "cognito-idp",
            endpoint_url=ctx.endpoint_url,
            region_name=ctx.region
        )

        if os.path.isfile('schema.graphql'):
            path = ''
        else:
            path = '../../'

        with open(f"{path}scalars.graphql") as f:
            self.schema = f.read()

        with open(f"{path}schema.graphql") as f:
            self.schema = f"{self.schema} {f.read()}"

    def call_lambda(self, payload: dict, function_name: str):
        json_payload = json.dumps(payload)
        resp = self.lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json_payload)
        if resp.get('StatusCode', None) == 200:
            return json.loads(resp['Payload'].read().decode("utf-8"))

        raise Exception(f"Call to lambda {function_name} failed")

    def authenticate(self, user: User):
        response = self.cognito_client.admin_initiate_auth(
            UserPoolId=user.user_pool_id,
            ClientId=user.client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': user.username,
                'PASSWORD': str(user.password)
            }
        )
        user.token = response['AuthenticationResult']['IdToken']
        return user

    def destroy(self):
        self.ctx = None
        self.session = None
        self.lambda_client = None
        AWSUtils._instances = {}


def create_user(ctx: TestContext,
                username: str = None,
                password: str = None,
                groups: list[str] = None,
                do_auth: bool = True):

    if username is None:
        username = generate_username()[0]

    if password is None:
        password = uuid4()

    if groups is None:
        groups = ALL_GROUPS

    payload = {
        "action": "create_user",
        "username": username,
        "email": f"{username}@example.com.invalid",
        "password": password,
        "groups": groups,
    }

    aws = AWSUtils(ctx)
    result = aws.call_lambda(payload=payload, function_name='example-local-devTestHelper')
    user = User(username=username, password=password, user_pool_id=result['userPoolId'], client_id=result['clientId'])
    if do_auth:
        user = authenticate(ctx=ctx, user=user)
    return user


def authenticate(ctx: TestContext, user: User) -> User:
    aws = AWSUtils(ctx)
    return aws.authenticate(user)


def get_gql_client(ctx: TestContext, user: User) -> Client:
    auth = AppSyncJWTAuthentication(
        host=ctx.host,
        jwt=user.token,
    )
    transport = AIOHTTPTransport(url=ctx.graphql_url, auth=auth)
    aws = AWSUtils(ctx=ctx)
    return Client(transport=transport, fetch_schema_from_transport=False, schema=aws.schema)


def query_gql(client: Client, query):
    if isinstance(query, str):
        q = gql(query)
    else:
        q = dsl_gql(query)

    try:
        result = client.execute(q)
        log.debug(result)
        return result
    except TransportQueryError as e:
        log.error(e)
        return e.errors


def do_gql(ctx: TestContext, user: User, query):
    client = get_gql_client(ctx, user)
    return query_gql(client=client, query=query)
