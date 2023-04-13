import logging as log
import os

import boto3

from lambdas import init_lambda
from lambdas.services.db_manager import with_db_session
from lambdas.utils import validators
from services.user_service import delete_user

aws_client = boto3.client(
    "cognito-idp", region_name=os.environ.get("AWS_REGION"))

init_lambda()


def get_aws_list(values: list[str]):
    result = ','.join(values)
    return f"[{result}]"


def create_user(username, password, email, groups: list[str]):
    user_pool_id = os.environ.get("USERPOOL_ID")
    client_id = os.environ.get("CLIENT_ID")
    aws_client.admin_create_user(
        UserPoolId=user_pool_id,
        Username=username,
        UserAttributes=[
            {"Name": "email", "Value": email},
            {"Name": "email_verified", "Value": "true"},
            {"Name": "custom:groups", "Value": get_aws_list(groups)},
        ],
        MessageAction="SUPPRESS",
        DesiredDeliveryMediums=["EMAIL"],
        TemporaryPassword=password,
    )

    aws_client.admin_set_user_password(
        UserPoolId=user_pool_id,
        Username=username,
        Password=password,
        Permanent=True
    )

    return {'username': username, 'status': 'Created', 'userPoolId': user_pool_id, 'clientId': client_id}


@with_db_session
def handler(event, _context):
    action = validators.get_event_value(
        event,
        "action",
        allowed_values=["create_user", "delete_user"]
    )

    if action == "create_user":
        username = validators.get_event_value(event, "username")
        log.debug("creating user %s", username)
        email = validators.get_event_value(event, "email")
        password = validators.get_event_value(event, "password")
        groups = validators.get_event_value(event, "groups")
        return create_user(username=username,
                           password=password,
                           email=email,
                           groups=groups)

    if action == "delete_user":
        username = validators.get_event_value(event, "username")
        log.debug("deleting user %s", username)
        aws_client.admin_delete_user(
            UserPoolId=os.environ.get("USERPOOL_ID"),
            Username=username,
        )
        delete_user(username)
        return "User deleted"

    raise Exception("Unknown action")
