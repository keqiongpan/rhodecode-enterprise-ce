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

from rhodecode.model.db import UserLog, PullRequest
from rhodecode.model.meta import Session
from rhodecode.tests import TEST_USER_ADMIN_LOGIN
from rhodecode.api.tests.utils import (
    build_data, api_call, assert_error, assert_ok)


@pytest.mark.usefixtures("testuser_api", "app")
class TestMergePullRequest(object):

    @pytest.mark.backends("git", "hg")
    def test_api_merge_pull_request_merge_failed(self, pr_util, no_notifications):
        pull_request = pr_util.create_pull_request(mergeable=True)
        pull_request_id = pull_request.pull_request_id
        pull_request_repo = pull_request.target_repo.repo_name

        id_, params = build_data(
            self.apikey, 'merge_pull_request',
            repoid=pull_request_repo,
            pullrequestid=pull_request_id)

        response = api_call(self.app, params)

        # The above api call detaches the pull request DB object from the
        # session because of an unconditional transaction rollback in our
        # middleware. Therefore we need to add it back here if we want to use it.
        Session().add(pull_request)

        expected = 'merge not possible for following reasons: ' \
                   'Pull request reviewer approval is pending.'
        assert_error(id_, expected, given=response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_merge_pull_request_merge_failed_disallowed_state(
            self, pr_util, no_notifications):
        pull_request = pr_util.create_pull_request(mergeable=True, approved=True)
        pull_request_id = pull_request.pull_request_id
        pull_request_repo = pull_request.target_repo.repo_name

        pr = PullRequest.get(pull_request_id)
        pr.pull_request_state = pull_request.STATE_UPDATING
        Session().add(pr)
        Session().commit()

        id_, params = build_data(
            self.apikey, 'merge_pull_request',
            repoid=pull_request_repo,
            pullrequestid=pull_request_id)

        response = api_call(self.app, params)
        expected = 'Operation forbidden because pull request is in state {}, '\
                   'only state {} is allowed.'.format(PullRequest.STATE_UPDATING,
                                                      PullRequest.STATE_CREATED)
        assert_error(id_, expected, given=response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_merge_pull_request(self, pr_util, no_notifications):
        pull_request = pr_util.create_pull_request(mergeable=True, approved=True)
        author = pull_request.user_id
        repo = pull_request.target_repo.repo_id
        pull_request_id = pull_request.pull_request_id
        pull_request_repo = pull_request.target_repo.repo_name

        id_, params = build_data(
            self.apikey, 'comment_pull_request',
            repoid=pull_request_repo,
            pullrequestid=pull_request_id,
            status='approved')

        response = api_call(self.app, params)
        expected = {
            'comment_id': response.json.get('result', {}).get('comment_id'),
            'pull_request_id': pull_request_id,
            'status': {'given': 'approved', 'was_changed': True}
        }
        assert_ok(id_, expected, given=response.body)

        id_, params = build_data(
            self.apikey, 'merge_pull_request',
            repoid=pull_request_repo,
            pullrequestid=pull_request_id)

        response = api_call(self.app, params)

        pull_request = PullRequest.get(pull_request_id)

        expected = {
            'executed': True,
            'failure_reason': 0,
            'possible': True,
            'merge_commit_id': pull_request.shadow_merge_ref.commit_id,
            'merge_ref': pull_request.shadow_merge_ref._asdict()
        }

        assert_ok(id_, expected, response.body)

        journal = UserLog.query()\
            .filter(UserLog.user_id == author)\
            .filter(UserLog.repository_id == repo) \
            .order_by('user_log_id') \
            .all()
        assert journal[-2].action == 'repo.pull_request.merge'
        assert journal[-1].action == 'repo.pull_request.close'

        id_, params = build_data(
            self.apikey, 'merge_pull_request',
            repoid=pull_request_repo, pullrequestid=pull_request_id)
        response = api_call(self.app, params)

        expected = 'merge not possible for following reasons: This pull request is closed.'
        assert_error(id_, expected, given=response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_merge_pull_request_repo_error(self, pr_util):
        pull_request = pr_util.create_pull_request()
        id_, params = build_data(
            self.apikey, 'merge_pull_request',
            repoid=666, pullrequestid=pull_request.pull_request_id)
        response = api_call(self.app, params)

        expected = 'repository `666` does not exist'
        assert_error(id_, expected, given=response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_merge_pull_request_non_admin_with_userid_error(self, pr_util):
        pull_request = pr_util.create_pull_request(mergeable=True)
        id_, params = build_data(
            self.apikey_regular, 'merge_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            userid=TEST_USER_ADMIN_LOGIN)
        response = api_call(self.app, params)

        expected = 'userid is not the same as your user'
        assert_error(id_, expected, given=response.body)
