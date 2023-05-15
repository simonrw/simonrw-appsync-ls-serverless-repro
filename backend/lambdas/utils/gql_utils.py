import logging as log
import os

from gql import Client, gql
from gql.dsl import dsl_gql
from gql.transport.exceptions import TransportQueryError


def query_gql(client: Client, query):
    if isinstance(query, str):
        qql_query = gql(query)
    else:
        qql_query = dsl_gql(query)

    try:
        result = client.execute(qql_query)
        log.debug(result)
        return result
    except TransportQueryError as e:
        log.error(e)
        return e.errors


def get_graphql_schema(base_path: str = ''):
    with open(f"{base_path}scalars.graphql", encoding="utf8") as file:
        schema = file.read()

    with open(f"{base_path}schema.graphql", encoding="utf8") as file:
        schema = f"{schema} {file.read()}"

    return schema
