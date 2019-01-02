# -*- coding: utf-8 -*-

# Copyright (C) 2016-2019 RhodeCode GmbH
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


from rhodecode.apps._base import ADMIN_PREFIX


def admin_routes(config):
    """
    Admin prefixed routes
    """

    config.add_route(
        name='admin_audit_logs',
        pattern='/audit_logs')

    config.add_route(
        name='admin_audit_log_entry',
        pattern='/audit_logs/{audit_log_id}')

    config.add_route(
        name='pull_requests_global_0',  # backward compat
        pattern='/pull_requests/{pull_request_id:\d+}')
    config.add_route(
        name='pull_requests_global_1',  # backward compat
        pattern='/pull-requests/{pull_request_id:\d+}')
    config.add_route(
        name='pull_requests_global',
        pattern='/pull-request/{pull_request_id:\d+}')

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
        name='admin_settings_exception_tracker',
        pattern='/settings/exceptions')
    config.add_route(
        name='admin_settings_exception_tracker_delete_all',
        pattern='/settings/exceptions/delete')
    config.add_route(
        name='admin_settings_exception_tracker_show',
        pattern='/settings/exceptions/{exception_id}')
    config.add_route(
        name='admin_settings_exception_tracker_delete',
        pattern='/settings/exceptions/{exception_id}/delete')

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
        name='admin_settings_process_management_data',
        pattern='/settings/process_management/data')
    config.add_route(
        name='admin_settings_process_management_signal',
        pattern='/settings/process_management/signal')
    config.add_route(
        name='admin_settings_process_management_master_signal',
        pattern='/settings/process_management/master_signal')

    # default settings
    config.add_route(
        name='admin_defaults_repositories',
        pattern='/defaults/repositories')
    config.add_route(
        name='admin_defaults_repositories_update',
        pattern='/defaults/repositories/update')

    # admin settings

    config.add_route(
        name='admin_settings',
        pattern='/settings')
    config.add_route(
        name='admin_settings_update',
        pattern='/settings/update')

    config.add_route(
        name='admin_settings_global',
        pattern='/settings/global')
    config.add_route(
        name='admin_settings_global_update',
        pattern='/settings/global/update')

    config.add_route(
        name='admin_settings_vcs',
        pattern='/settings/vcs')
    config.add_route(
        name='admin_settings_vcs_update',
        pattern='/settings/vcs/update')
    config.add_route(
        name='admin_settings_vcs_svn_pattern_delete',
        pattern='/settings/vcs/svn_pattern_delete')

    config.add_route(
        name='admin_settings_mapping',
        pattern='/settings/mapping')
    config.add_route(
        name='admin_settings_mapping_update',
        pattern='/settings/mapping/update')

    config.add_route(
        name='admin_settings_visual',
        pattern='/settings/visual')
    config.add_route(
        name='admin_settings_visual_update',
        pattern='/settings/visual/update')


    config.add_route(
        name='admin_settings_issuetracker',
        pattern='/settings/issue-tracker')
    config.add_route(
        name='admin_settings_issuetracker_update',
        pattern='/settings/issue-tracker/update')
    config.add_route(
        name='admin_settings_issuetracker_test',
        pattern='/settings/issue-tracker/test')
    config.add_route(
        name='admin_settings_issuetracker_delete',
        pattern='/settings/issue-tracker/delete')

    config.add_route(
        name='admin_settings_email',
        pattern='/settings/email')
    config.add_route(
        name='admin_settings_email_update',
        pattern='/settings/email/update')

    config.add_route(
        name='admin_settings_hooks',
        pattern='/settings/hooks')
    config.add_route(
        name='admin_settings_hooks_update',
        pattern='/settings/hooks/update')
    config.add_route(
        name='admin_settings_hooks_delete',
        pattern='/settings/hooks/delete')

    config.add_route(
        name='admin_settings_search',
        pattern='/settings/search')

    config.add_route(
        name='admin_settings_labs',
        pattern='/settings/labs')
    config.add_route(
        name='admin_settings_labs_update',
        pattern='/settings/labs/update')

    # Automation EE feature
    config.add_route(
        'admin_settings_automation',
        pattern=ADMIN_PREFIX + '/settings/automation')

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

    # Branch perms EE feature
    config.add_route(
        name='admin_permissions_branch',
        pattern='/permissions/branch')

    config.add_route(
        name='admin_permissions_ips',
        pattern='/permissions/ips')

    config.add_route(
        name='admin_permissions_overview',
        pattern='/permissions/overview')

    config.add_route(
        name='admin_permissions_auth_token_access',
        pattern='/permissions/auth_token_access')

    config.add_route(
        name='admin_permissions_ssh_keys',
        pattern='/permissions/ssh_keys')
    config.add_route(
        name='admin_permissions_ssh_keys_data',
        pattern='/permissions/ssh_keys/data')
    config.add_route(
        name='admin_permissions_ssh_keys_update',
        pattern='/permissions/ssh_keys/update')

    # users admin
    config.add_route(
        name='users',
        pattern='/users')

    config.add_route(
        name='users_data',
        pattern='/users_data')

    config.add_route(
        name='users_create',
        pattern='/users/create')

    config.add_route(
        name='users_new',
        pattern='/users/new')

    # user management
    config.add_route(
        name='user_edit',
        pattern='/users/{user_id:\d+}/edit',
        user_route=True)
    config.add_route(
        name='user_edit_advanced',
        pattern='/users/{user_id:\d+}/edit/advanced',
        user_route=True)
    config.add_route(
        name='user_edit_global_perms',
        pattern='/users/{user_id:\d+}/edit/global_permissions',
        user_route=True)
    config.add_route(
        name='user_edit_global_perms_update',
        pattern='/users/{user_id:\d+}/edit/global_permissions/update',
        user_route=True)
    config.add_route(
        name='user_update',
        pattern='/users/{user_id:\d+}/update',
        user_route=True)
    config.add_route(
        name='user_delete',
        pattern='/users/{user_id:\d+}/delete',
        user_route=True)
    config.add_route(
        name='user_force_password_reset',
        pattern='/users/{user_id:\d+}/password_reset',
        user_route=True)
    config.add_route(
        name='user_create_personal_repo_group',
        pattern='/users/{user_id:\d+}/create_repo_group',
        user_route=True)

    # user auth tokens
    config.add_route(
        name='edit_user_auth_tokens',
        pattern='/users/{user_id:\d+}/edit/auth_tokens',
        user_route=True)
    config.add_route(
        name='edit_user_auth_tokens_add',
        pattern='/users/{user_id:\d+}/edit/auth_tokens/new',
        user_route=True)
    config.add_route(
        name='edit_user_auth_tokens_delete',
        pattern='/users/{user_id:\d+}/edit/auth_tokens/delete',
        user_route=True)

    # user ssh keys
    config.add_route(
        name='edit_user_ssh_keys',
        pattern='/users/{user_id:\d+}/edit/ssh_keys',
        user_route=True)
    config.add_route(
        name='edit_user_ssh_keys_generate_keypair',
        pattern='/users/{user_id:\d+}/edit/ssh_keys/generate',
        user_route=True)
    config.add_route(
        name='edit_user_ssh_keys_add',
        pattern='/users/{user_id:\d+}/edit/ssh_keys/new',
        user_route=True)
    config.add_route(
        name='edit_user_ssh_keys_delete',
        pattern='/users/{user_id:\d+}/edit/ssh_keys/delete',
        user_route=True)

    # user emails
    config.add_route(
        name='edit_user_emails',
        pattern='/users/{user_id:\d+}/edit/emails',
        user_route=True)
    config.add_route(
        name='edit_user_emails_add',
        pattern='/users/{user_id:\d+}/edit/emails/new',
        user_route=True)
    config.add_route(
        name='edit_user_emails_delete',
        pattern='/users/{user_id:\d+}/edit/emails/delete',
        user_route=True)

    # user IPs
    config.add_route(
        name='edit_user_ips',
        pattern='/users/{user_id:\d+}/edit/ips',
        user_route=True)
    config.add_route(
        name='edit_user_ips_add',
        pattern='/users/{user_id:\d+}/edit/ips/new',
        user_route_with_default=True)  # enabled for default user too
    config.add_route(
        name='edit_user_ips_delete',
        pattern='/users/{user_id:\d+}/edit/ips/delete',
        user_route_with_default=True)  # enabled for default user too

    # user perms
    config.add_route(
        name='edit_user_perms_summary',
        pattern='/users/{user_id:\d+}/edit/permissions_summary',
        user_route=True)
    config.add_route(
        name='edit_user_perms_summary_json',
        pattern='/users/{user_id:\d+}/edit/permissions_summary/json',
        user_route=True)

    # user user groups management
    config.add_route(
        name='edit_user_groups_management',
        pattern='/users/{user_id:\d+}/edit/groups_management',
        user_route=True)

    config.add_route(
        name='edit_user_groups_management_updates',
        pattern='/users/{user_id:\d+}/edit/edit_user_groups_management/updates',
        user_route=True)

    # user audit logs
    config.add_route(
        name='edit_user_audit_logs',
        pattern='/users/{user_id:\d+}/edit/audit', user_route=True)

    # user caches
    config.add_route(
        name='edit_user_caches',
        pattern='/users/{user_id:\d+}/edit/caches',
        user_route=True)
    config.add_route(
        name='edit_user_caches_update',
        pattern='/users/{user_id:\d+}/edit/caches/update',
        user_route=True)

    # user-groups admin
    config.add_route(
        name='user_groups',
        pattern='/user_groups')

    config.add_route(
        name='user_groups_data',
        pattern='/user_groups_data')

    config.add_route(
        name='user_groups_new',
        pattern='/user_groups/new')

    config.add_route(
        name='user_groups_create',
        pattern='/user_groups/create')

    # repos admin
    config.add_route(
        name='repos',
        pattern='/repos')

    config.add_route(
        name='repo_new',
        pattern='/repos/new')

    config.add_route(
        name='repo_create',
        pattern='/repos/create')

    # repo groups admin
    config.add_route(
        name='repo_groups',
        pattern='/repo_groups')

    config.add_route(
        name='repo_group_new',
        pattern='/repo_group/new')

    config.add_route(
        name='repo_group_create',
        pattern='/repo_group/create')


def includeme(config):
    from rhodecode.apps._base.navigation import includeme as nav_includeme

    # Create admin navigation registry and add it to the pyramid registry.
    nav_includeme(config)

    # main admin routes
    config.add_route(name='admin_home', pattern=ADMIN_PREFIX)
    config.include(admin_routes, route_prefix=ADMIN_PREFIX)

    # Scan module for configuration decorators.
    config.scan('.views', ignore='.tests')
