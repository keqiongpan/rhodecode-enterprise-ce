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

import pytest

from . import assert_and_get_content
from rhodecode.tests import TestController, TEST_USER_ADMIN_LOGIN
from rhodecode.tests.fixture import Fixture

from rhodecode.lib.utils import map_groups
from rhodecode.model.repo import RepoModel
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.db import Session, Repository, RepoGroup

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'goto_switcher_data': '/_goto_data',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestGotoSwitcherData(TestController):

    required_repos_with_groups = [
        'abc',
        'abc-fork',
        'forks/abcd',
        'abcd',
        'abcde',
        'a/abc',
        'aa/abc',
        'aaa/abc',
        'aaaa/abc',
        'repos_abc/aaa/abc',
        'abc_repos/abc',
        'abc_repos/abcd',
        'xxx/xyz',
        'forked-abc/a/abc'
    ]

    @pytest.fixture(autouse=True, scope='class')
    def prepare(self, request, baseapp):
        for repo_and_group in self.required_repos_with_groups:
            # create structure of groups and return the last group

            repo_group = map_groups(repo_and_group)

            RepoModel()._create_repo(
                repo_and_group, 'hg', 'test-ac', TEST_USER_ADMIN_LOGIN,
                repo_group=getattr(repo_group, 'group_id', None))

            Session().commit()

        request.addfinalizer(self.cleanup)

    def cleanup(self):
        # first delete all repos
        for repo_and_groups in self.required_repos_with_groups:
            repo = Repository.get_by_repo_name(repo_and_groups)
            if repo:
                RepoModel().delete(repo)
                Session().commit()

        # then delete all empty groups
        for repo_and_groups in self.required_repos_with_groups:
            if '/' in repo_and_groups:
                r_group = repo_and_groups.rsplit('/', 1)[0]
                repo_group = RepoGroup.get_by_group_name(r_group)
                if not repo_group:
                    continue
                parents = repo_group.parents
                RepoGroupModel().delete(repo_group, force_delete=True)
                Session().commit()

                for el in reversed(parents):
                    RepoGroupModel().delete(el, force_delete=True)
                    Session().commit()

    def test_returns_list_of_repos_and_groups(self, xhr_header):
        self.log_user()

        response = self.app.get(
            route_path('goto_switcher_data'),
            extra_environ=xhr_header, status=200)
        result = json.loads(response.body)['results']

        repos, groups, commits = assert_and_get_content(result)

        assert len(repos) == len(Repository.get_all())
        assert len(groups) == len(RepoGroup.get_all())
        assert len(commits) == 0

    def test_returns_list_of_repos_and_groups_filtered(self, xhr_header):
        self.log_user()

        response = self.app.get(
            route_path('goto_switcher_data'),
            params={'query': 'abc'},
            extra_environ=xhr_header, status=200)
        result = json.loads(response.body)['results']

        repos, groups, commits = assert_and_get_content(result)

        assert len(repos) == 13
        assert len(groups) == 5
        assert len(commits) == 0

    def test_returns_list_of_properly_sorted_and_filtered(self, xhr_header):
        self.log_user()

        response = self.app.get(
            route_path('goto_switcher_data'),
            params={'query': 'abc'},
            extra_environ=xhr_header, status=200)
        result = json.loads(response.body)['results']

        repos, groups, commits = assert_and_get_content(result)

        test_repos = [x['text'] for x in repos[:4]]
        assert ['abc', 'abcd', 'a/abc', 'abcde'] == test_repos

        test_groups = [x['text'] for x in groups[:4]]
        assert ['abc_repos', 'repos_abc',
                'forked-abc', 'forked-abc/a'] == test_groups
