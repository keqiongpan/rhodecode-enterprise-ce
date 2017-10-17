# -*- coding: utf-8 -*-

# Copyright (C) 2010-2017 RhodeCode GmbH
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

from rhodecode.tests import assert_session_flash


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'edit_repo_group': '/{repo_group_name}/_edit',
        # Update is POST to the above url
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.usefixtures("app")
class TestRepoGroupsSettingsView(object):

    @pytest.mark.parametrize('repo_group_name', [
        'gro',
        u'12345',
    ])
    def test_edit(self, user_util, autologin_user, repo_group_name):
        user_util._test_name = repo_group_name
        repo_group = user_util.create_repo_group()

        self.app.get(
            route_path('edit_repo_group', repo_group_name=repo_group.group_name),
            status=200)

    def test_update(self, csrf_token, autologin_user, user_util, rc_fixture):
        repo_group = user_util.create_repo_group()
        repo_group_name = repo_group.group_name

        description = 'description for newly created repo group'
        form_data = rc_fixture._get_group_create_params(
            group_name=repo_group.group_name,
            group_description=description,
            csrf_token=csrf_token,
            repo_group_name=repo_group.group_name,
            repo_group_owner=repo_group.user.username)

        response = self.app.post(
            route_path('edit_repo_group',
                       repo_group_name=repo_group.group_name),
            form_data,
            status=302)

        assert_session_flash(
            response, 'Repository Group `{}` updated successfully'.format(
                repo_group_name))

    def test_update_fails_when_parent_pointing_to_self(
            self, csrf_token, user_util, autologin_user, rc_fixture):
        group = user_util.create_repo_group()
        response = self.app.post(
            route_path('edit_repo_group', repo_group_name=group.group_name),
            rc_fixture._get_group_create_params(
                repo_group_name=group.group_name,
                repo_group_owner=group.user.username,
                repo_group=group.group_id,
                csrf_token=csrf_token),
            status=200
            )
        response.mustcontain(
            '<span class="error-message">"{}" is not one of -1'.format(
                group.group_id))
