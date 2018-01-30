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

import json

from . import assert_and_get_content
from rhodecode.tests import TestController
from rhodecode.tests.fixture import Fixture
from rhodecode.model.db import Repository

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'repo_list_data': '/_repos',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestRepoListData(TestController):

    def test_returns_list_of_repos_and_groups(self, xhr_header):
        self.log_user()

        response = self.app.get(
            route_path('repo_list_data'),
            extra_environ=xhr_header, status=200)
        result = json.loads(response.body)['results']

        repos, groups, commits = assert_and_get_content(result)

        assert len(repos) == len(Repository.get_all())
        assert len(groups) == 0
        assert len(commits) == 0

    def test_returns_list_of_repos_and_groups_filtered(self, xhr_header):
        self.log_user()

        response = self.app.get(
            route_path('repo_list_data'),
            params={'query': 'vcs_test_git'},
            extra_environ=xhr_header, status=200)
        result = json.loads(response.body)['results']

        repos, groups, commits = assert_and_get_content(result)

        assert len(repos) == len(Repository.query().filter(
            Repository.repo_name.ilike('%vcs_test_git%')).all())
        assert len(groups) == 0
        assert len(commits) == 0

    def test_returns_list_of_repos_and_groups_filtered_with_type(self, xhr_header):
        self.log_user()

        response = self.app.get(
            route_path('repo_list_data'),
            params={'query': 'vcs_test_git', 'repo_type': 'git'},
            extra_environ=xhr_header, status=200)
        result = json.loads(response.body)['results']

        repos, groups, commits = assert_and_get_content(result)

        assert len(repos) == len(Repository.query().filter(
            Repository.repo_name.ilike('%vcs_test_git%')).all())
        assert len(groups) == 0
        assert len(commits) == 0

    def test_returns_list_of_repos_non_ascii_query(self, xhr_header):
        self.log_user()
        response = self.app.get(
            route_path('repo_list_data'),
            params={'query': 'ć_vcs_test_ą', 'repo_type': 'git'},
            extra_environ=xhr_header, status=200)
        result = json.loads(response.body)['results']

        repos, groups, commits = assert_and_get_content(result)

        assert len(repos) == 0
        assert len(groups) == 0
        assert len(commits) == 0
