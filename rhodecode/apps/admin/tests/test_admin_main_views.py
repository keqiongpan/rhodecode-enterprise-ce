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

from rhodecode.tests import TestController
from rhodecode.tests.fixture import Fixture

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib
    from rhodecode.apps._base import ADMIN_PREFIX

    base_url = {
        'admin_home': ADMIN_PREFIX,
        'pullrequest_show': '/{repo_name}/pull-request/{pull_request_id}',
        'pull_requests_global': ADMIN_PREFIX + '/pull-request/{pull_request_id}',
        'pull_requests_global_0': ADMIN_PREFIX + '/pull_requests/{pull_request_id}',
        'pull_requests_global_1': ADMIN_PREFIX + '/pull-requests/{pull_request_id}',

    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestAdminMainView(TestController):

    def test_access_admin_home(self):
        self.log_user()
        response = self.app.get(route_path('admin_home'), status=200)
        response.mustcontain("Administration area")

    def test_redirect_pull_request_view(self, view):
        self.log_user()
        self.app.get(
            route_path(view, pull_request_id='xxxx'),
            status=404)

    @pytest.mark.backends("git", "hg")
    @pytest.mark.parametrize('view', [
        'pull_requests_global',
        'pull_requests_global_0',
        'pull_requests_global_1',
    ])
    def test_redirect_pull_request_view(self, view, pr_util):
        self.log_user()
        pull_request = pr_util.create_pull_request()
        pull_request_id = pull_request.pull_request_id
        repo_name = pull_request.target_repo.repo_name

        response = self.app.get(
            route_path(view, pull_request_id=pull_request_id),
            status=302)
        assert response.location.endswith(
            'pull-request/{}'.format(pull_request_id))

        redirect_url = route_path(
            'pullrequest_show', repo_name=repo_name,
            pull_request_id=pull_request_id)

        assert redirect_url in response.location
