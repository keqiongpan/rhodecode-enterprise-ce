# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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

from rhodecode.lib.vcs.nodes import FileNode
from rhodecode.model.db import User
from rhodecode.model.pull_request import PullRequestModel
from rhodecode.tests import TEST_USER_ADMIN_LOGIN
from rhodecode.api.tests.utils import (
    build_data, api_call, assert_ok, assert_error)


@pytest.mark.usefixtures("testuser_api", "app")
class TestUpdatePullRequest(object):

    @pytest.mark.backends("git", "hg")
    def test_api_update_pull_request_title_or_description(
            self, pr_util, no_notifications):
        pull_request = pr_util.create_pull_request()

        id_, params = build_data(
            self.apikey, 'update_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            title='New TITLE OF A PR',
            description='New DESC OF A PR',
        )
        response = api_call(self.app, params)

        expected = {
            "msg": "Updated pull request `{}`".format(
                pull_request.pull_request_id),
            "pull_request": response.json['result']['pull_request'],
            "updated_commits": {"added": [], "common": [], "removed": []},
            "updated_reviewers": {"added": [], "removed": []},
            "updated_observers": {"added": [], "removed": []},
        }

        response_json = response.json['result']
        assert response_json == expected
        pr = response_json['pull_request']
        assert pr['title'] == 'New TITLE OF A PR'
        assert pr['description'] == 'New DESC OF A PR'

    @pytest.mark.backends("git", "hg")
    def test_api_try_update_closed_pull_request(
            self, pr_util, no_notifications):
        pull_request = pr_util.create_pull_request()
        PullRequestModel().close_pull_request(
            pull_request, TEST_USER_ADMIN_LOGIN)

        id_, params = build_data(
            self.apikey, 'update_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id)
        response = api_call(self.app, params)

        expected = 'pull request `{}` update failed, pull request ' \
                   'is closed'.format(pull_request.pull_request_id)

        assert_error(id_, expected, response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_update_update_commits(self, pr_util, no_notifications):
        commits = [
            {'message': 'a'},
            {'message': 'b', 'added': [FileNode('file_b', 'test_content\n')]},
            {'message': 'c', 'added': [FileNode('file_c', 'test_content\n')]},
        ]
        pull_request = pr_util.create_pull_request(
            commits=commits, target_head='a', source_head='b', revisions=['b'])
        pr_util.update_source_repository(head='c')
        repo = pull_request.source_repo.scm_instance()
        commits = [x for x in repo.get_commits()]

        added_commit_id = commits[-1].raw_id  # c commit
        common_commit_id = commits[1].raw_id  # b commit is common ancestor
        total_commits = [added_commit_id, common_commit_id]

        id_, params = build_data(
            self.apikey, 'update_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            update_commits=True
        )
        response = api_call(self.app, params)

        expected = {
            "msg": "Updated pull request `{}`".format(
                pull_request.pull_request_id),
            "pull_request": response.json['result']['pull_request'],
            "updated_commits": {"added": [added_commit_id],
                                "common": [common_commit_id],
                                "total": total_commits,
                                "removed": []},
            "updated_reviewers": {"added": [], "removed": []},
            "updated_observers": {"added": [], "removed": []},
        }

        assert_ok(id_, expected, response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_update_change_reviewers(
            self, user_util, pr_util, no_notifications):
        a = user_util.create_user()
        b = user_util.create_user()
        c = user_util.create_user()
        new_reviewers = [
            {'username': b.username, 'reasons': ['updated via API'],
             'mandatory':False},
            {'username': c.username, 'reasons': ['updated via API'],
             'mandatory':False},
        ]

        added = [b.username, c.username]
        removed = [a.username]

        pull_request = pr_util.create_pull_request(
            reviewers=[(a.username, ['added via API'], False, 'reviewer', [])])

        id_, params = build_data(
            self.apikey, 'update_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            reviewers=new_reviewers)
        response = api_call(self.app, params)
        expected = {
            "msg": "Updated pull request `{}`".format(
                pull_request.pull_request_id),
            "pull_request": response.json['result']['pull_request'],
            "updated_commits": {"added": [], "common": [], "removed": []},
            "updated_reviewers": {"added": added, "removed": removed},
            "updated_observers": {"added": [], "removed": []},
        }

        assert_ok(id_, expected, response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_update_bad_user_in_reviewers(self, pr_util):
        pull_request = pr_util.create_pull_request()

        id_, params = build_data(
            self.apikey, 'update_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            reviewers=[{'username': 'bad_name'}])
        response = api_call(self.app, params)

        expected = 'user `bad_name` does not exist'

        assert_error(id_, expected, response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_update_repo_error(self, pr_util):
        pull_request = pr_util.create_pull_request()
        id_, params = build_data(
            self.apikey, 'update_pull_request',
            repoid='fake',
            pullrequestid=pull_request.pull_request_id,
            reviewers=[{'username': 'bad_name'}])
        response = api_call(self.app, params)

        expected = 'repository `fake` does not exist'

        response_json = response.json['error']
        assert response_json == expected

    @pytest.mark.backends("git", "hg")
    def test_api_update_pull_request_error(self, pr_util):
        pull_request = pr_util.create_pull_request()

        id_, params = build_data(
            self.apikey, 'update_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=999999,
            reviewers=[{'username': 'bad_name'}])
        response = api_call(self.app, params)

        expected = 'pull request `999999` does not exist'
        assert_error(id_, expected, response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_update_pull_request_no_perms_to_update(
            self, user_util, pr_util):
        user = user_util.create_user()
        pull_request = pr_util.create_pull_request()

        id_, params = build_data(
            user.api_key, 'update_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,)
        response = api_call(self.app, params)

        expected = ('pull request `%s` update failed, '
                    'no permission to update.') % pull_request.pull_request_id

        assert_error(id_, expected, response.body)
