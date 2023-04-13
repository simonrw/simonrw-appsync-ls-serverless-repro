import json
import logging as log
import base64
import os

import boto3


class SecretsException(Exception):
    pass


def get_secret_value(name: str, result_type=str):
    log.debug("Fetching secret value for %s", name)
    env_var_name = name.upper().replace('-', '_')
    env_value = os.environ.get(env_var_name, None)
    if env_value is not None:
        if result_type == dict:
            return json.loads(env_value)
        return env_value

    log.debug("Retrieving secret value %s from AWS Secrets manager", name)

    region = os.environ.get('AWS_REGION', None)
    if region is None:
        raise SecretsException(f"Could not get AWS_REGION environment variable value while resolving {name}")

    log.info("Fetching AWS Secret value for %s", name)
    arn_variable = f"{env_var_name}_ARN"
    arn = os.environ.get(arn_variable, None)
    if arn is None:
        raise SecretsException(f"Secret arn environment variable {arn_variable} not defined")

    return get_secret(arn, region, result_type)


def get_secret(secret_name: str, region_name: str, result_type=str):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle
    # We rethrow the exception by default.

    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
    if 'SecretString' in get_secret_value_response:
        secret_value = get_secret_value_response['SecretString']
        if result_type == dict:
            return json.loads(secret_value)
        return secret_value

    return base64.b64decode(get_secret_value_response['SecretBinary'])
