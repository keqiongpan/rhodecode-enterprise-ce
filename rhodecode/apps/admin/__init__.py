# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017  RhodeCode GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3
# (only), as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This program is dual-licensed. If you wish to learn more about the
# RhodeCode Enterprise Edition, including its added features, Support services,
# and proprietary license terms, please see https://rhodecode.com/licenses/


from rhodecode.apps.admin.navigation import NavigationRegistry
from rhodecode.config.routing import ADMIN_PREFIX
from rhodecode.lib.utils2 import str2bool


def admin_routes(config):
    """
    Admin prefixed routes
    """

    config.add_route(
        name='admin_audit_logs',
        pattern='/audit_logs')

    config.add_route(
        name='pull_requests_global_0',  # backward compat
        pattern='/pull_requests/{pull_request_id:[0-9]+}')
    config.add_route(
        name='pull_requests_global_1',  # backward compat
        pattern='/pull-requests/{pull_request_id:[0-9]+}')
    config.add_route(
        name='pull_requests_global',
        pattern='/pull-request/{pull_request_id:[0-9]+}')

    config.add_route(
        name='admin_settings_open_source',
        pattern='/settings/open_source')
    config.add_route(
        name='admin_settings_vcs_svn_generate_cfg',
        pattern='/settings/vcs/svn_generate_cfg')

    config.add_route(
        name='admin_settings_system',
        pattern='/settings/system')
    config.add_route(
        name='admin_settings_system_update',
        pattern='/settings/system/updates')

    config.add_route(
        name='admin_settings_sessions',
        pattern='/settings/sessions')
    config.add_route(
        name='admin_settings_sessions_cleanup',
        pattern='/settings/sessions/cleanup')

    config.add_route(
        name='admin_settings_process_management',
        pattern='/settings/process_management')
    config.add_route(
        name='admin_settings_process_management_signal',
        pattern='/settings/process_management/signal')

    # global permissions

    config.add_route(
        name='admin_permissions_application',
        pattern='/permissions/application')
    config.add_route(
        name='admin_permissions_application_update',
        pattern='/permissions/application/update')

    config.add_route(
        name='admin_permissions_global',
        pattern='/permissions/global')
    config.add_route(
        name='admin_permissions_global_update',
        pattern='/permissions/global/update')

    config.add_route(
        name='admin_permissions_object',
        pattern='/permissions/object')
    config.add_route(
        name='admin_permissions_object_update',
        pattern='/permissions/object/update')

    config.add_route(
        name='admin_permissions_ips',
        pattern='/permissions/ips')

    config.add_route(
        name='admin_permissions_overview',
        pattern='/permissions/overview')

    config.add_route(
        name='admin_permissions_auth_token_access',
        pattern='/permissions/auth_token_access')

    # users admin
    config.add_route(
        name='users',
        pattern='/users')

    config.add_route(
        name='users_data',
        pattern='/users_data')

    # user auth tokens
    config.add_route(
        name='edit_user_auth_tokens',
        pattern='/users/{user_id:\d+}/edit/auth_tokens')
    config.add_route(
        name='edit_user_auth_tokens_add',
        pattern='/users/{user_id:\d+}/edit/auth_tokens/new')
    config.add_route(
        name='edit_user_auth_tokens_delete',
        pattern='/users/{user_id:\d+}/edit/auth_tokens/delete')

    # user emails
    config.add_route(
        name='edit_user_emails',
        pattern='/users/{user_id:\d+}/edit/emails')
    config.add_route(
        name='edit_user_emails_add',
        pattern='/users/{user_id:\d+}/edit/emails/new')
    config.add_route(
        name='edit_user_emails_delete',
        pattern='/users/{user_id:\d+}/edit/emails/delete')

    # user IPs
    config.add_route(
        name='edit_user_ips',
        pattern='/users/{user_id:\d+}/edit/ips')
    config.add_route(
        name='edit_user_ips_add',
        pattern='/users/{user_id:\d+}/edit/ips/new')
    config.add_route(
        name='edit_user_ips_delete',
        pattern='/users/{user_id:\d+}/edit/ips/delete')

    # user groups management
    config.add_route(
        name='edit_user_groups_management',
        pattern='/users/{user_id:\d+}/edit/groups_management')

    config.add_route(
        name='edit_user_groups_management_updates',
        pattern='/users/{user_id:\d+}/edit/edit_user_groups_management/updates')

    # user audit logs
    config.add_route(
        name='edit_user_audit_logs',
        pattern='/users/{user_id:\d+}/edit/audit')


def includeme(config):
    settings = config.get_settings()

    # Create admin navigation registry and add it to the pyramid registry.
    labs_active = str2bool(settings.get('labs_settings_active', False))
    navigation_registry = NavigationRegistry(labs_active=labs_active)
    config.registry.registerUtility(navigation_registry)

    # main admin routes
    config.add_route(name='admin_home', pattern=ADMIN_PREFIX)
    config.include(admin_routes, route_prefix=ADMIN_PREFIX)

    # Scan module for configuration decorators.
    config.scan()
