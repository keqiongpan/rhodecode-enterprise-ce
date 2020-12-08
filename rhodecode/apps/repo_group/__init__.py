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
from rhodecode.apps._base import add_route_with_slash
from rhodecode.apps.repo_group.views.repo_group_settings import RepoGroupSettingsView
from rhodecode.apps.repo_group.views.repo_group_advanced import RepoGroupAdvancedSettingsView
from rhodecode.apps.repo_group.views.repo_group_permissions import RepoGroupPermissionsView
from rhodecode.apps.home.views import HomeView


def includeme(config):

    # Settings
    config.add_route(
        name='edit_repo_group',
        pattern='/{repo_group_name:.*?[^/]}/_edit',
        repo_group_route=True)
    config.add_view(
        RepoGroupSettingsView,
        attr='edit_settings',
        route_name='edit_repo_group', request_method='GET',
        renderer='rhodecode:templates/admin/repo_groups/repo_group_edit.mako')
    config.add_view(
        RepoGroupSettingsView,
        attr='edit_settings_update',
        route_name='edit_repo_group', request_method='POST',
        renderer='rhodecode:templates/admin/repo_groups/repo_group_edit.mako')

    # Settings advanced
    config.add_route(
        name='edit_repo_group_advanced',
        pattern='/{repo_group_name:.*?[^/]}/_settings/advanced',
        repo_group_route=True)
    config.add_view(
        RepoGroupAdvancedSettingsView,
        attr='edit_repo_group_advanced',
        route_name='edit_repo_group_advanced', request_method='GET',
        renderer='rhodecode:templates/admin/repo_groups/repo_group_edit.mako')

    config.add_route(
        name='edit_repo_group_advanced_delete',
        pattern='/{repo_group_name:.*?[^/]}/_settings/advanced/delete',
        repo_group_route=True)
    config.add_view(
        RepoGroupAdvancedSettingsView,
        attr='edit_repo_group_delete',
        route_name='edit_repo_group_advanced_delete', request_method='POST',
        renderer='rhodecode:templates/admin/repo_groups/repo_group_edit.mako')

    # settings permissions
    config.add_route(
        name='edit_repo_group_perms',
        pattern='/{repo_group_name:.*?[^/]}/_settings/permissions',
        repo_group_route=True)
    config.add_view(
        RepoGroupPermissionsView,
        attr='edit_repo_group_permissions',
        route_name='edit_repo_group_perms', request_method='GET',
        renderer='rhodecode:templates/admin/repo_groups/repo_group_edit.mako')

    config.add_route(
        name='edit_repo_group_perms_update',
        pattern='/{repo_group_name:.*?[^/]}/_settings/permissions/update',
        repo_group_route=True)
    config.add_view(
        RepoGroupPermissionsView,
        attr='edit_repo_groups_permissions_update',
        route_name='edit_repo_group_perms_update', request_method='POST',
        renderer='rhodecode:templates/admin/repo_groups/repo_group_edit.mako')

    # Summary, NOTE(marcink): needs to be at the end for catch-all
    add_route_with_slash(
        config,
        name='repo_group_home',
        pattern='/{repo_group_name:.*?[^/]}', repo_group_route=True)
    config.add_view(
        HomeView,
        attr='repo_group_main_page',
        route_name='repo_group_home', request_method='GET',
        renderer='rhodecode:templates/index_repo_group.mako')
    config.add_view(
        HomeView,
        attr='repo_group_main_page',
        route_name='repo_group_home_slash', request_method='GET',
        renderer='rhodecode:templates/index_repo_group.mako')

