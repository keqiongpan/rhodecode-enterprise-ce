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
from rhodecode.apps._base import add_route_with_slash


def includeme(config):

    # Settings
    config.add_route(
        name='edit_repo_group',
        pattern='/{repo_group_name:.*?[^/]}/_edit',
        repo_group_route=True)
    # update is POST on edit_repo_group

    # Settings advanced
    config.add_route(
        name='edit_repo_group_advanced',
        pattern='/{repo_group_name:.*?[^/]}/_settings/advanced',
        repo_group_route=True)

    config.add_route(
        name='edit_repo_group_advanced_delete',
        pattern='/{repo_group_name:.*?[^/]}/_settings/advanced/delete',
        repo_group_route=True)

    # settings permissions
    config.add_route(
        name='edit_repo_group_perms',
        pattern='/{repo_group_name:.*?[^/]}/_settings/permissions',
        repo_group_route=True)

    config.add_route(
        name='edit_repo_group_perms_update',
        pattern='/{repo_group_name:.*?[^/]}/_settings/permissions/update',
        repo_group_route=True)

    # Summary, NOTE(marcink): needs to be at the end for catch-all
    add_route_with_slash(
        config,
        name='repo_group_home',
        pattern='/{repo_group_name:.*?[^/]}', repo_group_route=True)

    # Scan module for configuration decorators.
    config.scan('.views', ignore='.tests')
