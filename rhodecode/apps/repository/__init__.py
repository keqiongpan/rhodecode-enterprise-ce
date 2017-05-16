# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 RhodeCode GmbH
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


def includeme(config):

    # Summary
    config.add_route(
        name='repo_summary_explicit',
        pattern='/{repo_name:.*?[^/]}/summary', repo_route=True)

    # Tags
    config.add_route(
        name='tags_home',
        pattern='/{repo_name:.*?[^/]}/tags', repo_route=True)

    # Branches
    config.add_route(
        name='branches_home',
        pattern='/{repo_name:.*?[^/]}/branches', repo_route=True)

    # Bookmarks
    config.add_route(
        name='bookmarks_home',
        pattern='/{repo_name:.*?[^/]}/bookmarks', repo_route=True)

    # Settings
    config.add_route(
        name='edit_repo',
        pattern='/{repo_name:.*?[^/]}/settings', repo_route=True)

    # Settings advanced
    config.add_route(
        name='edit_repo_advanced',
        pattern='/{repo_name:.*?[^/]}/settings/advanced', repo_route=True)
    config.add_route(
        name='edit_repo_advanced_delete',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/delete', repo_route=True)
    config.add_route(
        name='edit_repo_advanced_locking',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/locking', repo_route=True)
    config.add_route(
        name='edit_repo_advanced_journal',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/journal', repo_route=True)
    config.add_route(
        name='edit_repo_advanced_fork',
        pattern='/{repo_name:.*?[^/]}/settings/advanced/fork', repo_route=True)

    # Caches
    config.add_route(
        name='edit_repo_caches',
        pattern='/{repo_name:.*?[^/]}/settings/caches', repo_route=True)

    # Permissions
    config.add_route(
        name='edit_repo_perms',
        pattern='/{repo_name:.*?[^/]}/settings/permissions', repo_route=True)

    # Repo Review Rules
    config.add_route(
        name='repo_reviewers',
        pattern='/{repo_name:.*?[^/]}/settings/review/rules', repo_route=True)

    # Maintenance
    config.add_route(
        name='repo_maintenance',
        pattern='/{repo_name:.*?[^/]}/settings/maintenance', repo_route=True)

    config.add_route(
        name='repo_maintenance_execute',
        pattern='/{repo_name:.*?[^/]}/settings/maintenance/execute', repo_route=True)

    # Strip
    config.add_route(
        name='strip',
        pattern='/{repo_name:.*?[^/]}/settings/strip', repo_route=True)

    config.add_route(
        name='strip_check',
        pattern='/{repo_name:.*?[^/]}/settings/strip_check', repo_route=True)

    config.add_route(
        name='strip_execute',
        pattern='/{repo_name:.*?[^/]}/settings/strip_execute', repo_route=True)

    # NOTE(marcink): needs to be at the end for catch-all
    # config.add_route(
    #     name='repo_summary',
    #     pattern='/{repo_name:.*?[^/]}', repo_route=True)

    # Scan module for configuration decorators.
    config.scan()
