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


def includeme(config):
    from rhodecode.apps.user_group_profile.views import UserGroupProfileView

    config.add_route(
        name='user_group_profile',
        pattern='/_profile_user_group/{user_group_name}')
    config.add_view(
        UserGroupProfileView,
        attr='user_group_profile',
        route_name='user_group_profile', request_method='GET',
        renderer='rhodecode:templates/user_group/user_group.mako')
