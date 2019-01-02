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

from rhodecode.tests import assert_session_flash


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'edit_repo_group_advanced':
            '/{repo_group_name}/_settings/advanced',
        'edit_repo_group_advanced_delete':
            '/{repo_group_name}/_settings/advanced/delete',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.usefixtures("app")
class TestRepoGroupsAdvancedView(object):

    @pytest.mark.parametrize('repo_group_name', [
        'gro',
        '12345',
    ])
    def test_show_advanced_settings(self, autologin_user, user_util, repo_group_name):
        user_util._test_name = repo_group_name
        gr = user_util.create_repo_group()
        self.app.get(
            route_path('edit_repo_group_advanced',
                       repo_group_name=gr.group_name))

    def test_show_advanced_settings_delete(self, autologin_user, user_util,
                                           csrf_token):
        gr = user_util.create_repo_group(auto_cleanup=False)
        repo_group_name = gr.group_name

        params = dict(
            csrf_token=csrf_token
        )
        response = self.app.post(
            route_path('edit_repo_group_advanced_delete',
                       repo_group_name=repo_group_name), params=params)
        assert_session_flash(
            response, 'Removed repository group `{}`'.format(repo_group_name))

    def test_delete_not_possible_with_objects_inside(self, autologin_user,
                                                     repo_groups, csrf_token):
        zombie_group, parent_group, child_group = repo_groups

        response = self.app.get(
            route_path('edit_repo_group_advanced',
                       repo_group_name=parent_group.group_name))

        response.mustcontain(
            'This repository group includes 1 children repository group')

        params = dict(
            csrf_token=csrf_token
        )
        response = self.app.post(
            route_path('edit_repo_group_advanced_delete',
                       repo_group_name=parent_group.group_name), params=params)

        assert_session_flash(
            response, 'This repository group contains 1 subgroup '
                      'and cannot be deleted')
