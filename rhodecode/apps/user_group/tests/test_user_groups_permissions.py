# -*- coding: utf-8 -*-

# Copyright (C) 2010-2019 RhodeCode GmbH
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

import pytest

from rhodecode.tests.utils import permission_update_data_generator


def route_path(name, params=None, **kwargs):
    import urllib
    from rhodecode.apps._base import ADMIN_PREFIX

    base_url = {
        'edit_user_group_perms':
            ADMIN_PREFIX + '/user_groups/{user_group_id}/edit/permissions',
        'edit_user_group_perms_update':
            ADMIN_PREFIX + '/user_groups/{user_group_id}/edit/permissions/update',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.usefixtures("app")
class TestUserGroupPermissionsView(object):

    def test_edit_perms_view(self, user_util, autologin_user):
        user_group = user_util.create_user_group()
        self.app.get(
            route_path('edit_user_group_perms',
                       user_group_id=user_group.users_group_id), status=200)

    def test_update_permissions(self, csrf_token, user_util):
        user_group = user_util.create_user_group()
        user_group_id = user_group.users_group_id
        user = user_util.create_user()
        user_id = user.user_id
        username = user.username

        # grant new
        form_data = permission_update_data_generator(
            csrf_token,
            default='usergroup.write',
            grant=[(user_id, 'usergroup.write', username, 'user')])

        response = self.app.post(
            route_path('edit_user_group_perms_update',
                       user_group_id=user_group_id), form_data).follow()

        assert 'User Group permissions updated' in response

        # revoke given
        form_data = permission_update_data_generator(
            csrf_token,
            default='usergroup.read',
            revoke=[(user_id, 'user')])

        response = self.app.post(
            route_path('edit_user_group_perms_update',
                       user_group_id=user_group_id), form_data).follow()

        assert 'User Group permissions updated' in response
