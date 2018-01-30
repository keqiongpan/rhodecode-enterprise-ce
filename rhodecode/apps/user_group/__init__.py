# -*- coding: utf-8 -*-

# Copyright (C) 2016-2018 RhodeCode GmbH
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
from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.lib.utils2 import str2bool


def admin_routes(config):
    """
    User groups /_admin prefixed routes
    """

    config.add_route(
        name='user_group_members_data',
        pattern='/user_groups/{user_group_id:\d+}/members',
        user_group_route=True)

    # user groups perms
    config.add_route(
        name='edit_user_group_perms_summary',
        pattern='/user_groups/{user_group_id:\d+}/edit/permissions_summary',
        user_group_route=True)
    config.add_route(
        name='edit_user_group_perms_summary_json',
        pattern='/user_groups/{user_group_id:\d+}/edit/permissions_summary/json',
        user_group_route=True)

    # user groups edit
    config.add_route(
        name='edit_user_group',
        pattern='/user_groups/{user_group_id:\d+}/edit',
        user_group_route=True)

    # user groups update
    config.add_route(
        name='user_groups_update',
        pattern='/user_groups/{user_group_id:\d+}/update',
        user_group_route=True)

    config.add_route(
        name='edit_user_group_global_perms',
        pattern='/user_groups/{user_group_id:\d+}/edit/global_permissions',
        user_group_route=True)

    config.add_route(
        name='edit_user_group_global_perms_update',
        pattern='/user_groups/{user_group_id:\d+}/edit/global_permissions/update',
        user_group_route=True)

    config.add_route(
        name='edit_user_group_perms',
        pattern='/user_groups/{user_group_id:\d+}/edit/permissions',
        user_group_route=True)

    config.add_route(
        name='edit_user_group_perms_update',
        pattern='/user_groups/{user_group_id:\d+}/edit/permissions/update',
        user_group_route=True)

    config.add_route(
        name='edit_user_group_advanced',
        pattern='/user_groups/{user_group_id:\d+}/edit/advanced',
        user_group_route=True)

    config.add_route(
        name='edit_user_group_advanced_sync',
        pattern='/user_groups/{user_group_id:\d+}/edit/advanced/sync',
        user_group_route=True)

    # user groups delete
    config.add_route(
        name='user_groups_delete',
        pattern='/user_groups/{user_group_id:\d+}/delete',
        user_group_route=True)


def includeme(config):
    # main admin routes
    config.include(admin_routes, route_prefix=ADMIN_PREFIX)

    # Scan module for configuration decorators.
    config.scan('.views', ignore='.tests')
