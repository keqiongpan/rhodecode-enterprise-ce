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
    from rhodecode.apps.ops.views import OpsView

    config.add_route(
        name='ops_ping',
        pattern='/ping')
    config.add_view(
        OpsView,
        attr='ops_ping',
        route_name='ops_ping', request_method='GET',
        renderer='json_ext')

    config.add_route(
        name='ops_error_test',
        pattern='/error')
    config.add_view(
        OpsView,
        attr='ops_error_test',
        route_name='ops_error_test', request_method='GET',
        renderer='json_ext')

    config.add_route(
        name='ops_redirect_test',
        pattern='/redirect')
    config.add_view(
        OpsView,
        attr='ops_redirect_test',
        route_name='ops_redirect_test', request_method='GET',
        renderer='json_ext')

    config.add_route(
        name='ops_healthcheck',
        pattern='/status')
    config.add_view(
        OpsView,
        attr='ops_healthcheck',
        route_name='ops_healthcheck', request_method='GET',
        renderer='json_ext')

def includeme(config):
    config.include(admin_routes, route_prefix=ADMIN_PREFIX + '/ops')
