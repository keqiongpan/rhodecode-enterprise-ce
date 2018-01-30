# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'edit_repo_group_perms':
            '/{repo_group_name:}/_settings/permissions',
        'edit_repo_group_perms_update':
            '/{repo_group_name}/_settings/permissions/update',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.usefixtures("app")
class TestRepoGroupsPermissionsView(object):

    def test_edit_repo_group_perms(self, user_util, autologin_user):
        repo_group = user_util.create_repo_group()
        self.app.get(
            route_path('edit_repo_group_perms',
                       repo_group_name=repo_group.group_name), status=200)

    def test_update_permissions(self):
        pass
