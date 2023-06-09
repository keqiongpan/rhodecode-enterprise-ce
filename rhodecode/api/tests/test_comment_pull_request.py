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

from rhodecode.model.comment import CommentsModel
from rhodecode.model.db import UserLog, User, ChangesetComment
from rhodecode.model.pull_request import PullRequestModel
from rhodecode.tests import TEST_USER_ADMIN_LOGIN
from rhodecode.api.tests.utils import (
    build_data, api_call, assert_error, assert_ok)


@pytest.mark.usefixtures("testuser_api", "app")
class TestCommentPullRequest(object):
    finalizers = []

    def teardown_method(self, method):
        if self.finalizers:
            for finalizer in self.finalizers:
                finalizer()
            self.finalizers = []

    @pytest.mark.backends("git", "hg")
    def test_api_comment_pull_request(self, pr_util, no_notifications):
        pull_request = pr_util.create_pull_request()
        pull_request_id = pull_request.pull_request_id
        author = pull_request.user_id
        repo = pull_request.target_repo.repo_id
        id_, params = build_data(
            self.apikey, 'comment_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            message='test message')
        response = api_call(self.app, params)
        pull_request = PullRequestModel().get(pull_request.pull_request_id)

        comments = CommentsModel().get_comments(
            pull_request.target_repo.repo_id, pull_request=pull_request)

        expected = {
            'pull_request_id': pull_request.pull_request_id,
            'comment_id': comments[-1].comment_id,
            'status': {'given': None, 'was_changed': None}
        }
        assert_ok(id_, expected, response.body)

        journal = UserLog.query()\
            .filter(UserLog.user_id == author)\
            .filter(UserLog.repository_id == repo) \
            .order_by(UserLog.user_log_id.asc()) \
            .all()
        assert journal[-1].action == 'repo.pull_request.comment.create'

    @pytest.mark.backends("git", "hg")
    def test_api_comment_pull_request_with_extra_recipients(self, pr_util, user_util):
        pull_request = pr_util.create_pull_request()

        user1 = user_util.create_user()
        user1_id = user1.user_id
        user2 = user_util.create_user()
        user2_id = user2.user_id

        id_, params = build_data(
            self.apikey, 'comment_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            message='test message',
            extra_recipients=[user1.user_id, user2.username]
        )
        response = api_call(self.app, params)
        pull_request = PullRequestModel().get(pull_request.pull_request_id)

        comments = CommentsModel().get_comments(
            pull_request.target_repo.repo_id, pull_request=pull_request)

        expected = {
            'pull_request_id': pull_request.pull_request_id,
            'comment_id': comments[-1].comment_id,
            'status': {'given': None, 'was_changed': None}
        }
        assert_ok(id_, expected, response.body)
        # check user1/user2 inbox for notification
        user1 = User.get(user1_id)
        assert 1 == len(user1.notifications)
        assert 'test message' in user1.notifications[0].notification.body

        user2 = User.get(user2_id)
        assert 1 == len(user2.notifications)
        assert 'test message' in user2.notifications[0].notification.body

    @pytest.mark.backends("git", "hg")
    def test_api_comment_pull_request_change_status(
            self, pr_util, no_notifications):
        pull_request = pr_util.create_pull_request()
        pull_request_id = pull_request.pull_request_id
        id_, params = build_data(
            self.apikey, 'comment_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            status='rejected')
        response = api_call(self.app, params)
        pull_request = PullRequestModel().get(pull_request_id)

        comments = CommentsModel().get_comments(
            pull_request.target_repo.repo_id, pull_request=pull_request)
        expected = {
            'pull_request_id': pull_request.pull_request_id,
            'comment_id': comments[-1].comment_id,
            'status':  {'given': 'rejected', 'was_changed': True}
        }
        assert_ok(id_, expected, response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_comment_pull_request_change_status_with_specific_commit_id(
            self, pr_util, no_notifications):
        pull_request = pr_util.create_pull_request()
        pull_request_id = pull_request.pull_request_id
        latest_commit_id = 'test_commit'
        # inject additional revision, to fail test the status change on
        # non-latest commit
        pull_request.revisions = pull_request.revisions + ['test_commit']

        id_, params = build_data(
            self.apikey, 'comment_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            status='approved', commit_id=latest_commit_id)
        response = api_call(self.app, params)
        pull_request = PullRequestModel().get(pull_request_id)

        expected = {
            'pull_request_id': pull_request.pull_request_id,
            'comment_id': None,
            'status':  {'given': 'approved', 'was_changed': False}
        }
        assert_ok(id_, expected, response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_comment_pull_request_change_status_with_specific_commit_id(
            self, pr_util, no_notifications):
        pull_request = pr_util.create_pull_request()
        pull_request_id = pull_request.pull_request_id
        latest_commit_id = pull_request.revisions[0]

        id_, params = build_data(
            self.apikey, 'comment_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            status='approved', commit_id=latest_commit_id)
        response = api_call(self.app, params)
        pull_request = PullRequestModel().get(pull_request_id)

        comments = CommentsModel().get_comments(
            pull_request.target_repo.repo_id, pull_request=pull_request)
        expected = {
            'pull_request_id': pull_request.pull_request_id,
            'comment_id': comments[-1].comment_id,
            'status':  {'given': 'approved', 'was_changed': True}
        }
        assert_ok(id_, expected, response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_comment_pull_request_missing_params_error(self, pr_util):
        pull_request = pr_util.create_pull_request()
        pull_request_id = pull_request.pull_request_id
        pull_request_repo = pull_request.target_repo.repo_name
        id_, params = build_data(
            self.apikey, 'comment_pull_request',
            repoid=pull_request_repo,
            pullrequestid=pull_request_id)
        response = api_call(self.app, params)

        expected = 'Both message and status parameters are missing. At least one is required.'
        assert_error(id_, expected, given=response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_comment_pull_request_unknown_status_error(self, pr_util):
        pull_request = pr_util.create_pull_request()
        pull_request_id = pull_request.pull_request_id
        pull_request_repo = pull_request.target_repo.repo_name
        id_, params = build_data(
            self.apikey, 'comment_pull_request',
            repoid=pull_request_repo,
            pullrequestid=pull_request_id,
            status='42')
        response = api_call(self.app, params)

        expected = 'Unknown comment status: `42`'
        assert_error(id_, expected, given=response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_comment_pull_request_repo_error(self, pr_util):
        pull_request = pr_util.create_pull_request()
        id_, params = build_data(
            self.apikey, 'comment_pull_request',
            repoid=666, pullrequestid=pull_request.pull_request_id)
        response = api_call(self.app, params)

        expected = 'repository `666` does not exist'
        assert_error(id_, expected, given=response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_comment_pull_request_non_admin_with_userid_error(self, pr_util):
        pull_request = pr_util.create_pull_request()
        id_, params = build_data(
            self.apikey_regular, 'comment_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            userid=TEST_USER_ADMIN_LOGIN)
        response = api_call(self.app, params)

        expected = 'userid is not the same as your user'
        assert_error(id_, expected, given=response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_comment_pull_request_non_admin_with_userid_error(self, pr_util):
        pull_request = pr_util.create_pull_request()
        id_, params = build_data(
            self.apikey_regular, 'comment_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            userid=TEST_USER_ADMIN_LOGIN)
        response = api_call(self.app, params)

        expected = 'userid is not the same as your user'
        assert_error(id_, expected, given=response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_comment_pull_request_wrong_commit_id_error(self, pr_util):
        pull_request = pr_util.create_pull_request()
        id_, params = build_data(
            self.apikey_regular, 'comment_pull_request',
            repoid=pull_request.target_repo.repo_name,
            status='approved',
            pullrequestid=pull_request.pull_request_id,
            commit_id='XXX')
        response = api_call(self.app, params)

        expected = 'Invalid commit_id `XXX` for this pull request.'
        assert_error(id_, expected, given=response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_edit_comment(self, pr_util):
        pull_request = pr_util.create_pull_request()

        id_, params = build_data(
            self.apikey,
            'comment_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            message='test message',
        )
        response = api_call(self.app, params)
        json_response = response.json
        comment_id = json_response['result']['comment_id']

        message_after_edit = 'just message'
        id_, params = build_data(
            self.apikey,
            'edit_comment',
            comment_id=comment_id,
            message=message_after_edit,
            version=0,
        )
        response = api_call(self.app, params)
        json_response = response.json
        assert json_response['result']['version'] == 1

        text_form_db = ChangesetComment.get(comment_id).text
        assert message_after_edit == text_form_db

    @pytest.mark.backends("git", "hg")
    def test_api_edit_comment_wrong_version(self, pr_util):
        pull_request = pr_util.create_pull_request()

        id_, params = build_data(
            self.apikey, 'comment_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            message='test message')
        response = api_call(self.app, params)
        json_response = response.json
        comment_id = json_response['result']['comment_id']

        message_after_edit = 'just message'
        id_, params = build_data(
            self.apikey_regular,
            'edit_comment',
            comment_id=comment_id,
            message=message_after_edit,
            version=1,
        )
        response = api_call(self.app, params)
        expected = 'comment ({}) version ({}) mismatch'.format(comment_id, 1)
        assert_error(id_, expected, given=response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_edit_comment_wrong_version(self, pr_util):
        pull_request = pr_util.create_pull_request()

        id_, params = build_data(
            self.apikey, 'comment_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request.pull_request_id,
            message='test message')
        response = api_call(self.app, params)
        json_response = response.json
        comment_id = json_response['result']['comment_id']

        id_, params = build_data(
            self.apikey,
            'edit_comment',
            comment_id=comment_id,
            message='',
            version=0,
        )
        response = api_call(self.app, params)
        expected = "comment ({}) can't be changed with empty string".format(comment_id, 1)
        assert_error(id_, expected, given=response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_edit_comment_wrong_user_set_by_non_admin(self, pr_util):
        pull_request = pr_util.create_pull_request()
        pull_request_id = pull_request.pull_request_id
        id_, params = build_data(
            self.apikey,
            'comment_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request_id,
            message='test message'
        )
        response = api_call(self.app, params)
        json_response = response.json
        comment_id = json_response['result']['comment_id']

        id_, params = build_data(
            self.apikey_regular,
            'edit_comment',
            comment_id=comment_id,
            message='just message',
            version=0,
            userid=TEST_USER_ADMIN_LOGIN
        )
        response = api_call(self.app, params)
        expected = 'userid is not the same as your user'
        assert_error(id_, expected, given=response.body)

    @pytest.mark.backends("git", "hg")
    def test_api_edit_comment_wrong_user_with_permissions_to_edit_comment(self, pr_util):
        pull_request = pr_util.create_pull_request()
        pull_request_id = pull_request.pull_request_id
        id_, params = build_data(
            self.apikey,
            'comment_pull_request',
            repoid=pull_request.target_repo.repo_name,
            pullrequestid=pull_request_id,
            message='test message'
        )
        response = api_call(self.app, params)
        json_response = response.json
        comment_id = json_response['result']['comment_id']

        id_, params = build_data(
            self.apikey_regular,
            'edit_comment',
            comment_id=comment_id,
            message='just message',
            version=0,
        )
        response = api_call(self.app, params)
        expected = "you don't have access to edit this comment"
        assert_error(id_, expected, given=response.body)
