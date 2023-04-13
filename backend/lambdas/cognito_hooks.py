import logging as log

from lambdas import init_lambda, ENVIRONMENT
from lambdas.services import user_service
from lambdas.services.db_manager import with_db_session

init_lambda()

PRE_TOKEN_GEN_PREFIX = "TokenGeneration"
POST_CONFIRMATION_PREFIX = "PostConfirmation"
POST_AUTH_PREFIX = "PostAuthentication"

PREFIX = f"{ENVIRONMENT}_" if ENVIRONMENT is not None and ENVIRONMENT != '' else ''


SUPPORTED_GROUPS = {'SYSADMIN'}


@with_db_session
def handler(event, _context):
    trigger_source: str = event['triggerSource']
    if trigger_source.startswith(PRE_TOKEN_GEN_PREFIX):
        return augment_token(event)
    if trigger_source.startswith('PostConfirmation') or trigger_source.startswith('PostAuthentication'):
        user_attributes = event['request']['userAttributes']
        user_name = event['userName']
        user_service.create_or_update_user(user_name, user_attributes)
        return event
    return event


def augment_token(event):
    custom_groups = parse_custom_groups(
        event.get('request', {})
        .get('userAttributes', {})
        .get('custom:groups', None))

    groups = custom_groups & SUPPORTED_GROUPS
    group_config = event['request']['groupConfiguration']
    groups_to_override: list = group_config['groupsToOverride']
    groups_to_override.extend(groups)

    event['response'] = {
        "claimsOverrideDetails": {
            "groupOverrideDetails": {
                "groupsToOverride": groups_to_override,
                "iamRolesToOverride": group_config['iamRolesToOverride'],
                "preferredRole": group_config['preferredRole']
            }
        }
    }
    return event


def parse_custom_groups(custom_groups: str) -> set[str]:
    log.debug("Parse custom groups %s", custom_groups)
    result = set()
    if custom_groups is not None:
        group_list = custom_groups.strip().strip('[').strip(']').split(',')
        for custom_group in group_list:
            group = custom_group.strip().removeprefix(PREFIX)
            result.add(group)
    return result
