# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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
    from rhodecode.apps.admin.views.audit_logs import AdminAuditLogsView
    from rhodecode.apps.admin.views.defaults import AdminDefaultSettingsView
    from rhodecode.apps.admin.views.exception_tracker import ExceptionsTrackerView
    from rhodecode.apps.admin.views.main_views import AdminMainView
    from rhodecode.apps.admin.views.open_source_licenses import OpenSourceLicensesAdminSettingsView
    from rhodecode.apps.admin.views.permissions import AdminPermissionsView
    from rhodecode.apps.admin.views.process_management import AdminProcessManagementView
    from rhodecode.apps.admin.views.repo_groups import AdminRepoGroupsView 
    from rhodecode.apps.admin.views.repositories import AdminReposView
    from rhodecode.apps.admin.views.sessions import AdminSessionSettingsView
    from rhodecode.apps.admin.views.settings import AdminSettingsView
    from rhodecode.apps.admin.views.svn_config import AdminSvnConfigView
    from rhodecode.apps.admin.views.system_info import AdminSystemInfoSettingsView
    from rhodecode.apps.admin.views.user_groups import AdminUserGroupsView
    from rhodecode.apps.admin.views.users import AdminUsersView, UsersView
    
    config.add_route(
        name='admin_audit_logs',
        pattern='/audit_logs')
    config.add_view(
        AdminAuditLogsView,
        attr='admin_audit_logs',
        route_name='admin_audit_logs', request_method='GET',
        renderer='rhodecode:templates/admin/admin_audit_logs.mako')

    config.add_route(
        name='admin_audit_log_entry',
        pattern='/audit_logs/{audit_log_id}')
    config.add_view(
        AdminAuditLogsView,
        attr='admin_audit_log_entry',
        route_name='admin_audit_log_entry', request_method='GET',
        renderer='rhodecode:templates/admin/admin_audit_log_entry.mako')

    config.add_route(
        name='admin_settings_open_source',
        pattern='/settings/open_source')
    config.add_view(
        OpenSourceLicensesAdminSettingsView,
        attr='open_source_licenses',
        route_name='admin_settings_open_source', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_vcs_svn_generate_cfg',
        pattern='/settings/vcs/svn_generate_cfg')
    config.add_view(
        AdminSvnConfigView,
        attr='vcs_svn_generate_config',
        route_name='admin_settings_vcs_svn_generate_cfg',
        request_method='POST', renderer='json')

    config.add_route(
        name='admin_settings_system',
        pattern='/settings/system')
    config.add_view(
        AdminSystemInfoSettingsView,
        attr='settings_system_info',
        route_name='admin_settings_system', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_system_update',
        pattern='/settings/system/updates')
    config.add_view(
        AdminSystemInfoSettingsView,
        attr='settings_system_info_check_update',
        route_name='admin_settings_system_update', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings_system_update.mako')

    config.add_route(
        name='admin_settings_exception_tracker',
        pattern='/settings/exceptions')
    config.add_view(
        ExceptionsTrackerView,
        attr='browse_exceptions',
        route_name='admin_settings_exception_tracker', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_exception_tracker_delete_all',
        pattern='/settings/exceptions_delete_all')
    config.add_view(
        ExceptionsTrackerView,
        attr='exception_delete_all',
        route_name='admin_settings_exception_tracker_delete_all', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_exception_tracker_show',
        pattern='/settings/exceptions/{exception_id}')
    config.add_view(
        ExceptionsTrackerView,
        attr='exception_show',
        route_name='admin_settings_exception_tracker_show', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_exception_tracker_delete',
        pattern='/settings/exceptions/{exception_id}/delete')
    config.add_view(
        ExceptionsTrackerView,
        attr='exception_delete',
        route_name='admin_settings_exception_tracker_delete', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_sessions',
        pattern='/settings/sessions')
    config.add_view(
        AdminSessionSettingsView,
        attr='settings_sessions',
        route_name='admin_settings_sessions', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_sessions_cleanup',
        pattern='/settings/sessions/cleanup')
    config.add_view(
        AdminSessionSettingsView,
        attr='settings_sessions_cleanup',
        route_name='admin_settings_sessions_cleanup', request_method='POST')

    config.add_route(
        name='admin_settings_process_management',
        pattern='/settings/process_management')
    config.add_view(
        AdminProcessManagementView,
        attr='process_management',
        route_name='admin_settings_process_management', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_process_management_data',
        pattern='/settings/process_management/data')
    config.add_view(
        AdminProcessManagementView,
        attr='process_management_data',
        route_name='admin_settings_process_management_data', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings_process_management_data.mako')

    config.add_route(
        name='admin_settings_process_management_signal',
        pattern='/settings/process_management/signal')
    config.add_view(
        AdminProcessManagementView,
        attr='process_management_signal',
        route_name='admin_settings_process_management_signal',
        request_method='POST', renderer='json_ext')

    config.add_route(
        name='admin_settings_process_management_master_signal',
        pattern='/settings/process_management/master_signal')
    config.add_view(
        AdminProcessManagementView,
        attr='process_management_master_signal',
        route_name='admin_settings_process_management_master_signal',
        request_method='POST', renderer='json_ext')

    # default settings
    config.add_route(
        name='admin_defaults_repositories',
        pattern='/defaults/repositories')
    config.add_view(
        AdminDefaultSettingsView,
        attr='defaults_repository_show',
        route_name='admin_defaults_repositories', request_method='GET',
        renderer='rhodecode:templates/admin/defaults/defaults.mako')

    config.add_route(
        name='admin_defaults_repositories_update',
        pattern='/defaults/repositories/update')
    config.add_view(
        AdminDefaultSettingsView,
        attr='defaults_repository_update',
        route_name='admin_defaults_repositories_update', request_method='POST',
        renderer='rhodecode:templates/admin/defaults/defaults.mako')

    # admin settings

    config.add_route(
        name='admin_settings',
        pattern='/settings')
    config.add_view(
        AdminSettingsView,
        attr='settings_global',
        route_name='admin_settings', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_update',
        pattern='/settings/update')
    config.add_view(
        AdminSettingsView,
        attr='settings_global_update',
        route_name='admin_settings_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_global',
        pattern='/settings/global')
    config.add_view(
        AdminSettingsView,
        attr='settings_global',
        route_name='admin_settings_global', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_global_update',
        pattern='/settings/global/update')
    config.add_view(
        AdminSettingsView,
        attr='settings_global_update',
        route_name='admin_settings_global_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_vcs',
        pattern='/settings/vcs')
    config.add_view(
        AdminSettingsView,
        attr='settings_vcs',
        route_name='admin_settings_vcs', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_vcs_update',
        pattern='/settings/vcs/update')
    config.add_view(
        AdminSettingsView,
        attr='settings_vcs_update',
        route_name='admin_settings_vcs_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_vcs_svn_pattern_delete',
        pattern='/settings/vcs/svn_pattern_delete')
    config.add_view(
        AdminSettingsView,
        attr='settings_vcs_delete_svn_pattern',
        route_name='admin_settings_vcs_svn_pattern_delete', request_method='POST',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='admin_settings_mapping',
        pattern='/settings/mapping')
    config.add_view(
        AdminSettingsView,
        attr='settings_mapping',
        route_name='admin_settings_mapping', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_mapping_update',
        pattern='/settings/mapping/update')
    config.add_view(
        AdminSettingsView,
        attr='settings_mapping_update',
        route_name='admin_settings_mapping_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_visual',
        pattern='/settings/visual')
    config.add_view(
        AdminSettingsView,
        attr='settings_visual',
        route_name='admin_settings_visual', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_visual_update',
        pattern='/settings/visual/update')
    config.add_view(
        AdminSettingsView,
        attr='settings_visual_update',
        route_name='admin_settings_visual_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_issuetracker',
        pattern='/settings/issue-tracker')
    config.add_view(
        AdminSettingsView,
        attr='settings_issuetracker',
        route_name='admin_settings_issuetracker', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_issuetracker_update',
        pattern='/settings/issue-tracker/update')
    config.add_view(
        AdminSettingsView,
        attr='settings_issuetracker_update',
        route_name='admin_settings_issuetracker_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_issuetracker_test',
        pattern='/settings/issue-tracker/test')
    config.add_view(
        AdminSettingsView,
        attr='settings_issuetracker_test',
        route_name='admin_settings_issuetracker_test', request_method='POST',
        renderer='string', xhr=True)

    config.add_route(
        name='admin_settings_issuetracker_delete',
        pattern='/settings/issue-tracker/delete')
    config.add_view(
        AdminSettingsView,
        attr='settings_issuetracker_delete',
        route_name='admin_settings_issuetracker_delete', request_method='POST',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='admin_settings_email',
        pattern='/settings/email')
    config.add_view(
        AdminSettingsView,
        attr='settings_email',
        route_name='admin_settings_email', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_email_update',
        pattern='/settings/email/update')
    config.add_view(
        AdminSettingsView,
        attr='settings_email_update',
        route_name='admin_settings_email_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_hooks',
        pattern='/settings/hooks')
    config.add_view(
        AdminSettingsView,
        attr='settings_hooks',
        route_name='admin_settings_hooks', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_hooks_update',
        pattern='/settings/hooks/update')
    config.add_view(
        AdminSettingsView,
        attr='settings_hooks_update',
        route_name='admin_settings_hooks_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_hooks_delete',
        pattern='/settings/hooks/delete')
    config.add_view(
        AdminSettingsView,
        attr='settings_hooks_update',
        route_name='admin_settings_hooks_delete', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_search',
        pattern='/settings/search')
    config.add_view(
        AdminSettingsView,
        attr='settings_search',
        route_name='admin_settings_search', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_labs',
        pattern='/settings/labs')
    config.add_view(
        AdminSettingsView,
        attr='settings_labs',
        route_name='admin_settings_labs', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    config.add_route(
        name='admin_settings_labs_update',
        pattern='/settings/labs/update')
    config.add_view(
        AdminSettingsView,
        attr='settings_labs_update',
        route_name='admin_settings_labs_update', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    # Automation EE feature
    config.add_route(
        'admin_settings_automation',
        pattern=ADMIN_PREFIX + '/settings/automation')
    config.add_view(
        AdminSettingsView,
        attr='settings_automation',
        route_name='admin_settings_automation', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')

    # global permissions

    config.add_route(
        name='admin_permissions_application',
        pattern='/permissions/application')
    config.add_view(
        AdminPermissionsView,
        attr='permissions_application',
        route_name='admin_permissions_application', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')

    config.add_route(
        name='admin_permissions_application_update',
        pattern='/permissions/application/update')
    config.add_view(
        AdminPermissionsView,
        attr='permissions_application_update',
        route_name='admin_permissions_application_update', request_method='POST',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')

    config.add_route(
        name='admin_permissions_global',
        pattern='/permissions/global')
    config.add_view(
        AdminPermissionsView,
        attr='permissions_global',
        route_name='admin_permissions_global', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')
    
    config.add_route(
        name='admin_permissions_global_update',
        pattern='/permissions/global/update')
    config.add_view(
        AdminPermissionsView,
        attr='permissions_global_update',
        route_name='admin_permissions_global_update', request_method='POST',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')

    config.add_route(
        name='admin_permissions_object',
        pattern='/permissions/object')
    config.add_view(
        AdminPermissionsView,
        attr='permissions_objects',
        route_name='admin_permissions_object', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')

    config.add_route(
        name='admin_permissions_object_update',
        pattern='/permissions/object/update')
    config.add_view(
        AdminPermissionsView,
        attr='permissions_objects_update',
        route_name='admin_permissions_object_update', request_method='POST',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')

    # Branch perms EE feature
    config.add_route(
        name='admin_permissions_branch',
        pattern='/permissions/branch')
    config.add_view(
        AdminPermissionsView,
        attr='permissions_branch',
        route_name='admin_permissions_branch', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')

    config.add_route(
        name='admin_permissions_ips',
        pattern='/permissions/ips')
    config.add_view(
        AdminPermissionsView,
        attr='permissions_ips',
        route_name='admin_permissions_ips', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')

    config.add_route(
        name='admin_permissions_overview',
        pattern='/permissions/overview')
    config.add_view(
        AdminPermissionsView,
        attr='permissions_overview',
        route_name='admin_permissions_overview', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')

    config.add_route(
        name='admin_permissions_auth_token_access',
        pattern='/permissions/auth_token_access')
    config.add_view(
        AdminPermissionsView,
        attr='auth_token_access',
        route_name='admin_permissions_auth_token_access', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')

    config.add_route(
        name='admin_permissions_ssh_keys',
        pattern='/permissions/ssh_keys')
    config.add_view(
        AdminPermissionsView,
        attr='ssh_keys',
        route_name='admin_permissions_ssh_keys', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')

    config.add_route(
        name='admin_permissions_ssh_keys_data',
        pattern='/permissions/ssh_keys/data')
    config.add_view(
        AdminPermissionsView,
        attr='ssh_keys_data',
        route_name='admin_permissions_ssh_keys_data', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='admin_permissions_ssh_keys_update',
        pattern='/permissions/ssh_keys/update')
    config.add_view(
        AdminPermissionsView,
        attr='ssh_keys_update',
        route_name='admin_permissions_ssh_keys_update', request_method='POST',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')

    # users admin
    config.add_route(
        name='users',
        pattern='/users')
    config.add_view(
        AdminUsersView,
        attr='users_list',
        route_name='users', request_method='GET',
        renderer='rhodecode:templates/admin/users/users.mako')

    config.add_route(
        name='users_data',
        pattern='/users_data')
    config.add_view(
        AdminUsersView,
        attr='users_list_data',
        # renderer defined below
        route_name='users_data', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='users_create',
        pattern='/users/create')
    config.add_view(
        AdminUsersView,
        attr='users_create',
        route_name='users_create', request_method='POST',
        renderer='rhodecode:templates/admin/users/user_add.mako')

    config.add_route(
        name='users_new',
        pattern='/users/new')
    config.add_view(
        AdminUsersView,
        attr='users_new',
        route_name='users_new', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_add.mako')

    # user management
    config.add_route(
        name='user_edit',
        pattern='/users/{user_id:\d+}/edit',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_edit',
        route_name='user_edit', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='user_edit_advanced',
        pattern='/users/{user_id:\d+}/edit/advanced',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_edit_advanced',
        route_name='user_edit_advanced', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='user_edit_global_perms',
        pattern='/users/{user_id:\d+}/edit/global_permissions',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_edit_global_perms',
        route_name='user_edit_global_perms', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='user_edit_global_perms_update',
        pattern='/users/{user_id:\d+}/edit/global_permissions/update',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_edit_global_perms_update',
        route_name='user_edit_global_perms_update', request_method='POST',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='user_update',
        pattern='/users/{user_id:\d+}/update',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_update',
        route_name='user_update', request_method='POST',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='user_delete',
        pattern='/users/{user_id:\d+}/delete',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_delete',
        route_name='user_delete', request_method='POST',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='user_enable_force_password_reset',
        pattern='/users/{user_id:\d+}/password_reset_enable',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_enable_force_password_reset',
        route_name='user_enable_force_password_reset', request_method='POST',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='user_disable_force_password_reset',
        pattern='/users/{user_id:\d+}/password_reset_disable',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_disable_force_password_reset',
        route_name='user_disable_force_password_reset', request_method='POST',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='user_create_personal_repo_group',
        pattern='/users/{user_id:\d+}/create_repo_group',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_create_personal_repo_group',
        route_name='user_create_personal_repo_group', request_method='POST',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    # user notice
    config.add_route(
        name='user_notice_dismiss',
        pattern='/users/{user_id:\d+}/notice_dismiss',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_notice_dismiss',
        route_name='user_notice_dismiss', request_method='POST',
        renderer='json_ext', xhr=True)

    # user auth tokens
    config.add_route(
        name='edit_user_auth_tokens',
        pattern='/users/{user_id:\d+}/edit/auth_tokens',
        user_route=True)
    config.add_view(
        UsersView,
        attr='auth_tokens',
        route_name='edit_user_auth_tokens', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='edit_user_auth_tokens_view',
        pattern='/users/{user_id:\d+}/edit/auth_tokens/view',
        user_route=True)
    config.add_view(
        UsersView,
        attr='auth_tokens_view',
        route_name='edit_user_auth_tokens_view', request_method='POST',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='edit_user_auth_tokens_add',
        pattern='/users/{user_id:\d+}/edit/auth_tokens/new',
        user_route=True)
    config.add_view(
        UsersView,
        attr='auth_tokens_add',
        route_name='edit_user_auth_tokens_add', request_method='POST')

    config.add_route(
        name='edit_user_auth_tokens_delete',
        pattern='/users/{user_id:\d+}/edit/auth_tokens/delete',
        user_route=True)
    config.add_view(
        UsersView,
        attr='auth_tokens_delete',
        route_name='edit_user_auth_tokens_delete', request_method='POST')

    # user ssh keys
    config.add_route(
        name='edit_user_ssh_keys',
        pattern='/users/{user_id:\d+}/edit/ssh_keys',
        user_route=True)
    config.add_view(
        UsersView,
        attr='ssh_keys',
        route_name='edit_user_ssh_keys', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='edit_user_ssh_keys_generate_keypair',
        pattern='/users/{user_id:\d+}/edit/ssh_keys/generate',
        user_route=True)
    config.add_view(
        UsersView,
        attr='ssh_keys_generate_keypair',
        route_name='edit_user_ssh_keys_generate_keypair', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='edit_user_ssh_keys_add',
        pattern='/users/{user_id:\d+}/edit/ssh_keys/new',
        user_route=True)
    config.add_view(
        UsersView,
        attr='ssh_keys_add',
        route_name='edit_user_ssh_keys_add', request_method='POST')

    config.add_route(
        name='edit_user_ssh_keys_delete',
        pattern='/users/{user_id:\d+}/edit/ssh_keys/delete',
        user_route=True)
    config.add_view(
        UsersView,
        attr='ssh_keys_delete',
        route_name='edit_user_ssh_keys_delete', request_method='POST')

    # user emails
    config.add_route(
        name='edit_user_emails',
        pattern='/users/{user_id:\d+}/edit/emails',
        user_route=True)
    config.add_view(
        UsersView,
        attr='emails',
        route_name='edit_user_emails', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='edit_user_emails_add',
        pattern='/users/{user_id:\d+}/edit/emails/new',
        user_route=True)
    config.add_view(
        UsersView,
        attr='emails_add',
        route_name='edit_user_emails_add', request_method='POST')

    config.add_route(
        name='edit_user_emails_delete',
        pattern='/users/{user_id:\d+}/edit/emails/delete',
        user_route=True)
    config.add_view(
        UsersView,
        attr='emails_delete',
        route_name='edit_user_emails_delete', request_method='POST')

    # user IPs
    config.add_route(
        name='edit_user_ips',
        pattern='/users/{user_id:\d+}/edit/ips',
        user_route=True)
    config.add_view(
        UsersView,
        attr='ips',
        route_name='edit_user_ips', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='edit_user_ips_add',
        pattern='/users/{user_id:\d+}/edit/ips/new',
        user_route_with_default=True)  # enabled for default user too
    config.add_view(
        UsersView,
        attr='ips_add',
        route_name='edit_user_ips_add', request_method='POST')

    config.add_route(
        name='edit_user_ips_delete',
        pattern='/users/{user_id:\d+}/edit/ips/delete',
        user_route_with_default=True)  # enabled for default user too
    config.add_view(
        UsersView,
        attr='ips_delete',
        route_name='edit_user_ips_delete', request_method='POST')

    # user perms
    config.add_route(
        name='edit_user_perms_summary',
        pattern='/users/{user_id:\d+}/edit/permissions_summary',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_perms_summary',
        route_name='edit_user_perms_summary', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='edit_user_perms_summary_json',
        pattern='/users/{user_id:\d+}/edit/permissions_summary/json',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_perms_summary_json',
        route_name='edit_user_perms_summary_json', request_method='GET',
        renderer='json_ext')

    # user user groups management
    config.add_route(
        name='edit_user_groups_management',
        pattern='/users/{user_id:\d+}/edit/groups_management',
        user_route=True)
    config.add_view(
        UsersView,
        attr='groups_management',
        route_name='edit_user_groups_management', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='edit_user_groups_management_updates',
        pattern='/users/{user_id:\d+}/edit/edit_user_groups_management/updates',
        user_route=True)
    config.add_view(
        UsersView,
        attr='groups_management_updates',
        route_name='edit_user_groups_management_updates', request_method='POST')

    # user audit logs
    config.add_route(
        name='edit_user_audit_logs',
        pattern='/users/{user_id:\d+}/edit/audit', user_route=True)
    config.add_view(
        UsersView,
        attr='user_audit_logs',
        route_name='edit_user_audit_logs', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='edit_user_audit_logs_download',
        pattern='/users/{user_id:\d+}/edit/audit/download', user_route=True)
    config.add_view(
        UsersView,
        attr='user_audit_logs_download',
        route_name='edit_user_audit_logs_download', request_method='GET',
        renderer='string')

    # user caches
    config.add_route(
        name='edit_user_caches',
        pattern='/users/{user_id:\d+}/edit/caches',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_caches',
        route_name='edit_user_caches', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')

    config.add_route(
        name='edit_user_caches_update',
        pattern='/users/{user_id:\d+}/edit/caches/update',
        user_route=True)
    config.add_view(
        UsersView,
        attr='user_caches_update',
        route_name='edit_user_caches_update', request_method='POST')

    # user-groups admin
    config.add_route(
        name='user_groups',
        pattern='/user_groups')
    config.add_view(
        AdminUserGroupsView,
        attr='user_groups_list',
        route_name='user_groups', request_method='GET',
        renderer='rhodecode:templates/admin/user_groups/user_groups.mako')

    config.add_route(
        name='user_groups_data',
        pattern='/user_groups_data')
    config.add_view(
        AdminUserGroupsView,
        attr='user_groups_list_data',
        route_name='user_groups_data', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='user_groups_new',
        pattern='/user_groups/new')
    config.add_view(
        AdminUserGroupsView,
        attr='user_groups_new',
        route_name='user_groups_new', request_method='GET',
        renderer='rhodecode:templates/admin/user_groups/user_group_add.mako')

    config.add_route(
        name='user_groups_create',
        pattern='/user_groups/create')
    config.add_view(
        AdminUserGroupsView,
        attr='user_groups_create',
        route_name='user_groups_create', request_method='POST',
        renderer='rhodecode:templates/admin/user_groups/user_group_add.mako')

    # repos admin
    config.add_route(
        name='repos',
        pattern='/repos')
    config.add_view(
        AdminReposView,
        attr='repository_list',
        route_name='repos', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repos.mako')

    config.add_route(
        name='repos_data',
        pattern='/repos_data')
    config.add_view(
        AdminReposView,
        attr='repository_list_data',
        route_name='repos_data', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='repo_new',
        pattern='/repos/new')
    config.add_view(
        AdminReposView,
        attr='repository_new',
        route_name='repo_new', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_add.mako')

    config.add_route(
        name='repo_create',
        pattern='/repos/create')
    config.add_view(
        AdminReposView,
        attr='repository_create',
        route_name='repo_create', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repos.mako')

    # repo groups admin
    config.add_route(
        name='repo_groups',
        pattern='/repo_groups')
    config.add_view(
        AdminRepoGroupsView,
        attr='repo_group_list',
        route_name='repo_groups', request_method='GET',
        renderer='rhodecode:templates/admin/repo_groups/repo_groups.mako')

    config.add_route(
        name='repo_groups_data',
        pattern='/repo_groups_data')
    config.add_view(
        AdminRepoGroupsView,
        attr='repo_group_list_data',
        route_name='repo_groups_data', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='repo_group_new',
        pattern='/repo_group/new')
    config.add_view(
        AdminRepoGroupsView,
        attr='repo_group_new',
        route_name='repo_group_new', request_method='GET',
        renderer='rhodecode:templates/admin/repo_groups/repo_group_add.mako')

    config.add_route(
        name='repo_group_create',
        pattern='/repo_group/create')
    config.add_view(
        AdminRepoGroupsView,
        attr='repo_group_create',
        route_name='repo_group_create', request_method='POST',
        renderer='rhodecode:templates/admin/repo_groups/repo_group_add.mako')


def includeme(config):
    from rhodecode.apps._base.navigation import includeme as nav_includeme
    from rhodecode.apps.admin.views.main_views import AdminMainView

    # Create admin navigation registry and add it to the pyramid registry.
    nav_includeme(config)

    # main admin routes
    config.add_route(
        name='admin_home', pattern=ADMIN_PREFIX)
    config.add_view(
        AdminMainView,
        attr='admin_main',
        route_name='admin_home', request_method='GET',
        renderer='rhodecode:templates/admin/main.mako')

    # pr global redirect
    config.add_route(
        name='pull_requests_global_0',  # backward compat
        pattern=ADMIN_PREFIX + '/pull_requests/{pull_request_id:\d+}')
    config.add_view(
        AdminMainView,
        attr='pull_requests',
        route_name='pull_requests_global_0', request_method='GET')

    config.add_route(
        name='pull_requests_global_1',  # backward compat
        pattern=ADMIN_PREFIX + '/pull-requests/{pull_request_id:\d+}')
    config.add_view(
        AdminMainView,
        attr='pull_requests',
        route_name='pull_requests_global_1', request_method='GET')

    config.add_route(
        name='pull_requests_global',
        pattern=ADMIN_PREFIX + '/pull-request/{pull_request_id:\d+}')
    config.add_view(
        AdminMainView,
        attr='pull_requests',
        route_name='pull_requests_global', request_method='GET')

    config.include(admin_routes, route_prefix=ADMIN_PREFIX)
