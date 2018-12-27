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
import mock
import pytest

import rhodecode
from rhodecode.lib.vcs.backends.base import MergeResponse, MergeFailureReason
from rhodecode.lib.vcs.nodes import FileNode
from rhodecode.lib import helpers as h
from rhodecode.model.changeset_status import ChangesetStatusModel
from rhodecode.model.db import (
    PullRequest, ChangesetStatus, UserLog, Notification, ChangesetComment, Repository)
from rhodecode.model.meta import Session
from rhodecode.model.pull_request import PullRequestModel
from rhodecode.model.user import UserModel
from rhodecode.tests import (
    assert_session_flash, TEST_USER_ADMIN_LOGIN, TEST_USER_REGULAR_LOGIN)
from rhodecode.tests.utils import AssertResponse


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'repo_changelog': '/{repo_name}/changelog',
        'repo_changelog_file': '/{repo_name}/changelog/{commit_id}/{f_path}',
        'pullrequest_show': '/{repo_name}/pull-request/{pull_request_id}',
        'pullrequest_show_all': '/{repo_name}/pull-request',
        'pullrequest_show_all_data': '/{repo_name}/pull-request-data',
        'pullrequest_repo_refs': '/{repo_name}/pull-request/refs/{target_repo_name:.*?[^/]}',
        'pullrequest_repo_targets': '/{repo_name}/pull-request/repo-destinations',
        'pullrequest_new': '/{repo_name}/pull-request/new',
        'pullrequest_create': '/{repo_name}/pull-request/create',
        'pullrequest_update': '/{repo_name}/pull-request/{pull_request_id}/update',
        'pullrequest_merge': '/{repo_name}/pull-request/{pull_request_id}/merge',
        'pullrequest_delete': '/{repo_name}/pull-request/{pull_request_id}/delete',
        'pullrequest_comment_create': '/{repo_name}/pull-request/{pull_request_id}/comment',
        'pullrequest_comment_delete': '/{repo_name}/pull-request/{pull_request_id}/comment/{comment_id}/delete',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.usefixtures('app', 'autologin_user')
@pytest.mark.backends("git", "hg")
class TestPullrequestsView(object):

    def test_index(self, backend):
        self.app.get(route_path(
            'pullrequest_new',
            repo_name=backend.repo_name))

    def test_option_menu_create_pull_request_exists(self, backend):
        repo_name = backend.repo_name
        response = self.app.get(h.route_path('repo_summary', repo_name=repo_name))

        create_pr_link = '<a href="%s">Create Pull Request</a>' % route_path(
            'pullrequest_new', repo_name=repo_name)
        response.mustcontain(create_pr_link)

    def test_create_pr_form_with_raw_commit_id(self, backend):
        repo = backend.repo

        self.app.get(
            route_path('pullrequest_new', repo_name=repo.repo_name,
                       commit=repo.get_commit().raw_id),
            status=200)

    @pytest.mark.parametrize('pr_merge_enabled', [True, False])
    @pytest.mark.parametrize('range_diff', ["0", "1"])
    def test_show(self, pr_util, pr_merge_enabled, range_diff):
        pull_request = pr_util.create_pull_request(
            mergeable=pr_merge_enabled, enable_notifications=False)

        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id,
            params={'range-diff': range_diff}))

        for commit_id in pull_request.revisions:
            response.mustcontain(commit_id)

        assert pull_request.target_ref_parts.type in response
        assert pull_request.target_ref_parts.name in response
        target_clone_url = pull_request.target_repo.clone_url()
        assert target_clone_url in response

        assert 'class="pull-request-merge"' in response
        if pr_merge_enabled:
            response.mustcontain('Pull request reviewer approval is pending')
        else:
            response.mustcontain('Server-side pull request merging is disabled.')

        if range_diff == "1":
            response.mustcontain('Turn off: Show the diff as commit range')

    def test_close_status_visibility(self, pr_util, user_util, csrf_token):
        # Logout
        response = self.app.post(
            h.route_path('logout'),
            params={'csrf_token': csrf_token})
        # Login as regular user
        response = self.app.post(h.route_path('login'),
                                 {'username': TEST_USER_REGULAR_LOGIN,
                                  'password': 'test12'})

        pull_request = pr_util.create_pull_request(
            author=TEST_USER_REGULAR_LOGIN)

        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id))

        response.mustcontain('Server-side pull request merging is disabled.')

        assert_response = response.assert_response()
        # for regular user without a merge permissions, we don't see it
        assert_response.no_element_exists('#close-pull-request-action')

        user_util.grant_user_permission_to_repo(
            pull_request.target_repo,
            UserModel().get_by_username(TEST_USER_REGULAR_LOGIN),
            'repository.write')
        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id))

        response.mustcontain('Server-side pull request merging is disabled.')

        assert_response = response.assert_response()
        # now regular user has a merge permissions, we have CLOSE button
        assert_response.one_element_exists('#close-pull-request-action')

    def test_show_invalid_commit_id(self, pr_util):
        # Simulating invalid revisions which will cause a lookup error
        pull_request = pr_util.create_pull_request()
        pull_request.revisions = ['invalid']
        Session().add(pull_request)
        Session().commit()

        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id))

        for commit_id in pull_request.revisions:
            response.mustcontain(commit_id)

    def test_show_invalid_source_reference(self, pr_util):
        pull_request = pr_util.create_pull_request()
        pull_request.source_ref = 'branch:b:invalid'
        Session().add(pull_request)
        Session().commit()

        self.app.get(route_path(
            'pullrequest_show',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id))

    def test_edit_title_description(self, pr_util, csrf_token):
        pull_request = pr_util.create_pull_request()
        pull_request_id = pull_request.pull_request_id

        response = self.app.post(
            route_path('pullrequest_update',
                repo_name=pull_request.target_repo.repo_name,
                pull_request_id=pull_request_id),
            params={
                'edit_pull_request': 'true',
                'title': 'New title',
                'description': 'New description',
                'csrf_token': csrf_token})

        assert_session_flash(
            response, u'Pull request title & description updated.',
            category='success')

        pull_request = PullRequest.get(pull_request_id)
        assert pull_request.title == 'New title'
        assert pull_request.description == 'New description'

    def test_edit_title_description_closed(self, pr_util, csrf_token):
        pull_request = pr_util.create_pull_request()
        pull_request_id = pull_request.pull_request_id
        repo_name = pull_request.target_repo.repo_name
        pr_util.close()

        response = self.app.post(
            route_path('pullrequest_update',
                       repo_name=repo_name, pull_request_id=pull_request_id),
            params={
                'edit_pull_request': 'true',
                'title': 'New title',
                'description': 'New description',
                'csrf_token': csrf_token}, status=200)
        assert_session_flash(
            response, u'Cannot update closed pull requests.',
            category='error')

    def test_update_invalid_source_reference(self, pr_util, csrf_token):
        from rhodecode.lib.vcs.backends.base import UpdateFailureReason

        pull_request = pr_util.create_pull_request()
        pull_request.source_ref = 'branch:invalid-branch:invalid-commit-id'
        Session().add(pull_request)
        Session().commit()

        pull_request_id = pull_request.pull_request_id

        response = self.app.post(
            route_path('pullrequest_update',
                repo_name=pull_request.target_repo.repo_name,
                pull_request_id=pull_request_id),
            params={'update_commits': 'true',
                    'csrf_token': csrf_token})

        expected_msg = str(PullRequestModel.UPDATE_STATUS_MESSAGES[
            UpdateFailureReason.MISSING_SOURCE_REF])
        assert_session_flash(response, expected_msg, category='error')

    def test_missing_target_reference(self, pr_util, csrf_token):
        from rhodecode.lib.vcs.backends.base import MergeFailureReason
        pull_request = pr_util.create_pull_request(
            approved=True, mergeable=True)
        pull_request.target_ref = 'branch:invalid-branch:invalid-commit-id'
        Session().add(pull_request)
        Session().commit()

        pull_request_id = pull_request.pull_request_id
        pull_request_url = route_path(
            'pullrequest_show',
            repo_name=pull_request.target_repo.repo_name,
            pull_request_id=pull_request_id)

        response = self.app.get(pull_request_url)

        assertr = AssertResponse(response)
        expected_msg = PullRequestModel.MERGE_STATUS_MESSAGES[
            MergeFailureReason.MISSING_TARGET_REF]
        assertr.element_contains(
            'span[data-role="merge-message"]', str(expected_msg))

    def test_comment_and_close_pull_request_custom_message_approved(
            self, pr_util, csrf_token, xhr_header):

        pull_request = pr_util.create_pull_request(approved=True)
        pull_request_id = pull_request.pull_request_id
        author = pull_request.user_id
        repo = pull_request.target_repo.repo_id

        self.app.post(
            route_path('pullrequest_comment_create',
                repo_name=pull_request.target_repo.scm_instance().name,
                pull_request_id=pull_request_id),
            params={
                'close_pull_request': '1',
                'text': 'Closing a PR',
                'csrf_token': csrf_token},
            extra_environ=xhr_header,)

        journal = UserLog.query()\
            .filter(UserLog.user_id == author)\
            .filter(UserLog.repository_id == repo) \
            .order_by('user_log_id') \
            .all()
        assert journal[-1].action == 'repo.pull_request.close'

        pull_request = PullRequest.get(pull_request_id)
        assert pull_request.is_closed()

        status = ChangesetStatusModel().get_status(
            pull_request.source_repo, pull_request=pull_request)
        assert status == ChangesetStatus.STATUS_APPROVED
        comments = ChangesetComment().query() \
            .filter(ChangesetComment.pull_request == pull_request) \
            .order_by(ChangesetComment.comment_id.asc())\
            .all()
        assert comments[-1].text == 'Closing a PR'

    def test_comment_force_close_pull_request_rejected(
            self, pr_util, csrf_token, xhr_header):
        pull_request = pr_util.create_pull_request()
        pull_request_id = pull_request.pull_request_id
        PullRequestModel().update_reviewers(
            pull_request_id, [(1, ['reason'], False, []), (2, ['reason2'], False, [])],
            pull_request.author)
        author = pull_request.user_id
        repo = pull_request.target_repo.repo_id

        self.app.post(
            route_path('pullrequest_comment_create',
                repo_name=pull_request.target_repo.scm_instance().name,
                pull_request_id=pull_request_id),
            params={
                'close_pull_request': '1',
                'csrf_token': csrf_token},
            extra_environ=xhr_header)

        pull_request = PullRequest.get(pull_request_id)

        journal = UserLog.query()\
            .filter(UserLog.user_id == author, UserLog.repository_id == repo) \
            .order_by('user_log_id') \
            .all()
        assert journal[-1].action == 'repo.pull_request.close'

        # check only the latest status, not the review status
        status = ChangesetStatusModel().get_status(
            pull_request.source_repo, pull_request=pull_request)
        assert status == ChangesetStatus.STATUS_REJECTED

    def test_comment_and_close_pull_request(
            self, pr_util, csrf_token, xhr_header):
        pull_request = pr_util.create_pull_request()
        pull_request_id = pull_request.pull_request_id

        response = self.app.post(
            route_path('pullrequest_comment_create',
                repo_name=pull_request.target_repo.scm_instance().name,
                pull_request_id=pull_request.pull_request_id),
            params={
                'close_pull_request': 'true',
                'csrf_token': csrf_token},
            extra_environ=xhr_header)

        assert response.json

        pull_request = PullRequest.get(pull_request_id)
        assert pull_request.is_closed()

        # check only the latest status, not the review status
        status = ChangesetStatusModel().get_status(
            pull_request.source_repo, pull_request=pull_request)
        assert status == ChangesetStatus.STATUS_REJECTED

    def test_create_pull_request(self, backend, csrf_token):
        commits = [
            {'message': 'ancestor'},
            {'message': 'change'},
            {'message': 'change2'},
        ]
        commit_ids = backend.create_master_repo(commits)
        target = backend.create_repo(heads=['ancestor'])
        source = backend.create_repo(heads=['change2'])

        response = self.app.post(
            route_path('pullrequest_create', repo_name=source.repo_name),
            [
                ('source_repo', source.repo_name),
                ('source_ref', 'branch:default:' + commit_ids['change2']),
                ('target_repo', target.repo_name),
                ('target_ref',  'branch:default:' + commit_ids['ancestor']),
                ('common_ancestor', commit_ids['ancestor']),
                ('pullrequest_title', 'Title'),
                ('pullrequest_desc', 'Description'),
                ('description_renderer', 'markdown'),
                ('__start__', 'review_members:sequence'),
                    ('__start__', 'reviewer:mapping'),
                        ('user_id', '1'),
                        ('__start__', 'reasons:sequence'),
                            ('reason', 'Some reason'),
                        ('__end__', 'reasons:sequence'),
                        ('__start__', 'rules:sequence'),
                        ('__end__', 'rules:sequence'),
                        ('mandatory', 'False'),
                    ('__end__', 'reviewer:mapping'),
                ('__end__', 'review_members:sequence'),
                ('__start__', 'revisions:sequence'),
                    ('revisions', commit_ids['change']),
                    ('revisions', commit_ids['change2']),
                ('__end__', 'revisions:sequence'),
                ('user', ''),
                ('csrf_token', csrf_token),
            ],
            status=302)

        location = response.headers['Location']
        pull_request_id = location.rsplit('/', 1)[1]
        assert pull_request_id != 'new'
        pull_request = PullRequest.get(int(pull_request_id))

        # check that we have now both revisions
        assert pull_request.revisions == [commit_ids['change2'], commit_ids['change']]
        assert pull_request.source_ref == 'branch:default:' + commit_ids['change2']
        expected_target_ref = 'branch:default:' + commit_ids['ancestor']
        assert pull_request.target_ref == expected_target_ref

    def test_reviewer_notifications(self, backend, csrf_token):
        # We have to use the app.post for this test so it will create the
        # notifications properly with the new PR
        commits = [
            {'message': 'ancestor',
             'added': [FileNode('file_A', content='content_of_ancestor')]},
            {'message': 'change',
             'added': [FileNode('file_a', content='content_of_change')]},
            {'message': 'change-child'},
            {'message': 'ancestor-child', 'parents': ['ancestor'],
             'added': [
                FileNode('file_B', content='content_of_ancestor_child')]},
            {'message': 'ancestor-child-2'},
        ]
        commit_ids = backend.create_master_repo(commits)
        target = backend.create_repo(heads=['ancestor-child'])
        source = backend.create_repo(heads=['change'])

        response = self.app.post(
            route_path('pullrequest_create', repo_name=source.repo_name),
            [
                ('source_repo', source.repo_name),
                ('source_ref', 'branch:default:' + commit_ids['change']),
                ('target_repo', target.repo_name),
                ('target_ref',  'branch:default:' + commit_ids['ancestor-child']),
                ('common_ancestor', commit_ids['ancestor']),
                ('pullrequest_title', 'Title'),
                ('pullrequest_desc', 'Description'),
                ('description_renderer', 'markdown'),
                ('__start__', 'review_members:sequence'),
                    ('__start__', 'reviewer:mapping'),
                        ('user_id', '2'),
                        ('__start__', 'reasons:sequence'),
                            ('reason', 'Some reason'),
                        ('__end__', 'reasons:sequence'),
                        ('__start__', 'rules:sequence'),
                        ('__end__', 'rules:sequence'),
                        ('mandatory', 'False'),
                    ('__end__', 'reviewer:mapping'),
                ('__end__', 'review_members:sequence'),
                ('__start__', 'revisions:sequence'),
                    ('revisions', commit_ids['change']),
                ('__end__', 'revisions:sequence'),
                ('user', ''),
                ('csrf_token', csrf_token),
            ],
            status=302)

        location = response.headers['Location']

        pull_request_id = location.rsplit('/', 1)[1]
        assert pull_request_id != 'new'
        pull_request = PullRequest.get(int(pull_request_id))

        # Check that a notification was made
        notifications = Notification.query()\
            .filter(Notification.created_by == pull_request.author.user_id,
                    Notification.type_ == Notification.TYPE_PULL_REQUEST,
                    Notification.subject.contains(
                        "wants you to review pull request #%s" % pull_request_id))
        assert len(notifications.all()) == 1

        # Change reviewers and check that a notification was made
        PullRequestModel().update_reviewers(
            pull_request.pull_request_id, [(1, [], False, [])],
            pull_request.author)
        assert len(notifications.all()) == 2

    def test_create_pull_request_stores_ancestor_commit_id(self, backend,
                                                           csrf_token):
        commits = [
            {'message': 'ancestor',
             'added': [FileNode('file_A', content='content_of_ancestor')]},
            {'message': 'change',
             'added': [FileNode('file_a', content='content_of_change')]},
            {'message': 'change-child'},
            {'message': 'ancestor-child', 'parents': ['ancestor'],
             'added': [
                FileNode('file_B', content='content_of_ancestor_child')]},
            {'message': 'ancestor-child-2'},
        ]
        commit_ids = backend.create_master_repo(commits)
        target = backend.create_repo(heads=['ancestor-child'])
        source = backend.create_repo(heads=['change'])

        response = self.app.post(
            route_path('pullrequest_create', repo_name=source.repo_name),
            [
                ('source_repo', source.repo_name),
                ('source_ref', 'branch:default:' + commit_ids['change']),
                ('target_repo', target.repo_name),
                ('target_ref',  'branch:default:' + commit_ids['ancestor-child']),
                ('common_ancestor', commit_ids['ancestor']),
                ('pullrequest_title', 'Title'),
                ('pullrequest_desc', 'Description'),
                ('description_renderer', 'markdown'),
                ('__start__', 'review_members:sequence'),
                    ('__start__', 'reviewer:mapping'),
                        ('user_id', '1'),
                        ('__start__', 'reasons:sequence'),
                            ('reason', 'Some reason'),
                        ('__end__', 'reasons:sequence'),
                        ('__start__', 'rules:sequence'),
                        ('__end__', 'rules:sequence'),
                        ('mandatory', 'False'),
                    ('__end__', 'reviewer:mapping'),
                ('__end__', 'review_members:sequence'),
                ('__start__', 'revisions:sequence'),
                    ('revisions', commit_ids['change']),
                ('__end__', 'revisions:sequence'),
                ('user', ''),
                ('csrf_token', csrf_token),
            ],
            status=302)

        location = response.headers['Location']

        pull_request_id = location.rsplit('/', 1)[1]
        assert pull_request_id != 'new'
        pull_request = PullRequest.get(int(pull_request_id))

        # target_ref has to point to the ancestor's commit_id in order to
        # show the correct diff
        expected_target_ref = 'branch:default:' + commit_ids['ancestor']
        assert pull_request.target_ref == expected_target_ref

        # Check generated diff contents
        response = response.follow()
        assert 'content_of_ancestor' not in response.body
        assert 'content_of_ancestor-child' not in response.body
        assert 'content_of_change' in response.body

    def test_merge_pull_request_enabled(self, pr_util, csrf_token):
        # Clear any previous calls to rcextensions
        rhodecode.EXTENSIONS.calls.clear()

        pull_request = pr_util.create_pull_request(
            approved=True, mergeable=True)
        pull_request_id = pull_request.pull_request_id
        repo_name = pull_request.target_repo.scm_instance().name,

        response = self.app.post(
            route_path('pullrequest_merge',
                repo_name=str(repo_name[0]),
                pull_request_id=pull_request_id),
            params={'csrf_token': csrf_token}).follow()

        pull_request = PullRequest.get(pull_request_id)

        assert response.status_int == 200
        assert pull_request.is_closed()
        assert_pull_request_status(
            pull_request, ChangesetStatus.STATUS_APPROVED)

        # Check the relevant log entries were added
        user_logs = UserLog.query().order_by('-user_log_id').limit(3)
        actions = [log.action for log in user_logs]
        pr_commit_ids = PullRequestModel()._get_commit_ids(pull_request)
        expected_actions = [
             u'repo.pull_request.close',
             u'repo.pull_request.merge',
             u'repo.pull_request.comment.create'
        ]
        assert actions == expected_actions

        user_logs = UserLog.query().order_by('-user_log_id').limit(4)
        actions = [log for log in user_logs]
        assert actions[-1].action == 'user.push'
        assert actions[-1].action_data['commit_ids'] == pr_commit_ids

        # Check post_push rcextension was really executed
        push_calls = rhodecode.EXTENSIONS.calls['_push_hook']
        assert len(push_calls) == 1
        unused_last_call_args, last_call_kwargs = push_calls[0]
        assert last_call_kwargs['action'] == 'push'
        assert last_call_kwargs['commit_ids'] == pr_commit_ids

    def test_merge_pull_request_disabled(self, pr_util, csrf_token):
        pull_request = pr_util.create_pull_request(mergeable=False)
        pull_request_id = pull_request.pull_request_id
        pull_request = PullRequest.get(pull_request_id)

        response = self.app.post(
            route_path('pullrequest_merge',
                repo_name=pull_request.target_repo.scm_instance().name,
                pull_request_id=pull_request.pull_request_id),
            params={'csrf_token': csrf_token}).follow()

        assert response.status_int == 200
        response.mustcontain(
            'Merge is not currently possible because of below failed checks.')
        response.mustcontain('Server-side pull request merging is disabled.')

    @pytest.mark.skip_backends('svn')
    def test_merge_pull_request_not_approved(self, pr_util, csrf_token):
        pull_request = pr_util.create_pull_request(mergeable=True)
        pull_request_id = pull_request.pull_request_id
        repo_name = pull_request.target_repo.scm_instance().name

        response = self.app.post(
            route_path('pullrequest_merge',
                repo_name=repo_name,
                pull_request_id=pull_request_id),
            params={'csrf_token': csrf_token}).follow()

        assert response.status_int == 200

        response.mustcontain(
            'Merge is not currently possible because of below failed checks.')
        response.mustcontain('Pull request reviewer approval is pending.')

    def test_merge_pull_request_renders_failure_reason(
            self, user_regular, csrf_token, pr_util):
        pull_request = pr_util.create_pull_request(mergeable=True, approved=True)
        pull_request_id = pull_request.pull_request_id
        repo_name = pull_request.target_repo.scm_instance().name

        model_patcher = mock.patch.multiple(
            PullRequestModel,
            merge_repo=mock.Mock(return_value=MergeResponse(
                True, False, 'STUB_COMMIT_ID', MergeFailureReason.PUSH_FAILED)),
            merge_status=mock.Mock(return_value=(True, 'WRONG_MESSAGE')))

        with model_patcher:
            response = self.app.post(
                route_path('pullrequest_merge',
                           repo_name=repo_name,
                           pull_request_id=pull_request_id),
                params={'csrf_token': csrf_token}, status=302)

        assert_session_flash(response, PullRequestModel.MERGE_STATUS_MESSAGES[
            MergeFailureReason.PUSH_FAILED])

    def test_update_source_revision(self, backend, csrf_token):
        commits = [
            {'message': 'ancestor'},
            {'message': 'change'},
            {'message': 'change-2'},
        ]
        commit_ids = backend.create_master_repo(commits)
        target = backend.create_repo(heads=['ancestor'])
        source = backend.create_repo(heads=['change'])

        # create pr from a in source to A in target
        pull_request = PullRequest()
        pull_request.source_repo = source
        # TODO: johbo: Make sure that we write the source ref this way!
        pull_request.source_ref = 'branch:{branch}:{commit_id}'.format(
            branch=backend.default_branch_name, commit_id=commit_ids['change'])
        pull_request.target_repo = target

        pull_request.target_ref = 'branch:{branch}:{commit_id}'.format(
            branch=backend.default_branch_name,
            commit_id=commit_ids['ancestor'])
        pull_request.revisions = [commit_ids['change']]
        pull_request.title = u"Test"
        pull_request.description = u"Description"
        pull_request.author = UserModel().get_by_username(
            TEST_USER_ADMIN_LOGIN)
        Session().add(pull_request)
        Session().commit()
        pull_request_id = pull_request.pull_request_id

        # source has ancestor - change - change-2
        backend.pull_heads(source, heads=['change-2'])

        # update PR
        self.app.post(
            route_path('pullrequest_update',
                repo_name=target.repo_name,
                pull_request_id=pull_request_id),
            params={'update_commits': 'true',
                    'csrf_token': csrf_token})

        # check that we have now both revisions
        pull_request = PullRequest.get(pull_request_id)
        assert pull_request.revisions == [
            commit_ids['change-2'], commit_ids['change']]

        # TODO: johbo: this should be a test on its own
        response = self.app.get(route_path(
            'pullrequest_new',
            repo_name=target.repo_name))
        assert response.status_int == 200
        assert 'Pull request updated to' in response.body
        assert 'with 1 added, 0 removed commits.' in response.body

    def test_update_target_revision(self, backend, csrf_token):
        commits = [
            {'message': 'ancestor'},
            {'message': 'change'},
            {'message': 'ancestor-new', 'parents': ['ancestor']},
            {'message': 'change-rebased'},
        ]
        commit_ids = backend.create_master_repo(commits)
        target = backend.create_repo(heads=['ancestor'])
        source = backend.create_repo(heads=['change'])

        # create pr from a in source to A in target
        pull_request = PullRequest()
        pull_request.source_repo = source
        # TODO: johbo: Make sure that we write the source ref this way!
        pull_request.source_ref = 'branch:{branch}:{commit_id}'.format(
            branch=backend.default_branch_name, commit_id=commit_ids['change'])
        pull_request.target_repo = target
        # TODO: johbo: Target ref should be branch based, since tip can jump
        # from branch to branch
        pull_request.target_ref = 'branch:{branch}:{commit_id}'.format(
            branch=backend.default_branch_name,
            commit_id=commit_ids['ancestor'])
        pull_request.revisions = [commit_ids['change']]
        pull_request.title = u"Test"
        pull_request.description = u"Description"
        pull_request.author = UserModel().get_by_username(
            TEST_USER_ADMIN_LOGIN)
        Session().add(pull_request)
        Session().commit()
        pull_request_id = pull_request.pull_request_id

        # target has ancestor - ancestor-new
        # source has ancestor - ancestor-new - change-rebased
        backend.pull_heads(target, heads=['ancestor-new'])
        backend.pull_heads(source, heads=['change-rebased'])

        # update PR
        self.app.post(
            route_path('pullrequest_update',
                repo_name=target.repo_name,
                pull_request_id=pull_request_id),
            params={'update_commits': 'true',
                    'csrf_token': csrf_token},
            status=200)

        # check that we have now both revisions
        pull_request = PullRequest.get(pull_request_id)
        assert pull_request.revisions == [commit_ids['change-rebased']]
        assert pull_request.target_ref == 'branch:{branch}:{commit_id}'.format(
            branch=backend.default_branch_name,
            commit_id=commit_ids['ancestor-new'])

        # TODO: johbo: This should be a test on its own
        response = self.app.get(route_path(
            'pullrequest_new',
            repo_name=target.repo_name))
        assert response.status_int == 200
        assert 'Pull request updated to' in response.body
        assert 'with 1 added, 1 removed commits.' in response.body

    def test_update_target_revision_with_removal_of_1_commit_git(self, backend_git, csrf_token):
        backend = backend_git
        commits = [
            {'message': 'master-commit-1'},
            {'message': 'master-commit-2-change-1'},
            {'message': 'master-commit-3-change-2'},

            {'message': 'feat-commit-1', 'parents': ['master-commit-1']},
            {'message': 'feat-commit-2'},
        ]
        commit_ids = backend.create_master_repo(commits)
        target = backend.create_repo(heads=['master-commit-3-change-2'])
        source = backend.create_repo(heads=['feat-commit-2'])

        # create pr from a in source to A in target
        pull_request = PullRequest()
        pull_request.source_repo = source
        # TODO: johbo: Make sure that we write the source ref this way!
        pull_request.source_ref = 'branch:{branch}:{commit_id}'.format(
            branch=backend.default_branch_name,
            commit_id=commit_ids['master-commit-3-change-2'])

        pull_request.target_repo = target
        # TODO: johbo: Target ref should be branch based, since tip can jump
        # from branch to branch
        pull_request.target_ref = 'branch:{branch}:{commit_id}'.format(
            branch=backend.default_branch_name,
            commit_id=commit_ids['feat-commit-2'])

        pull_request.revisions = [
            commit_ids['feat-commit-1'],
            commit_ids['feat-commit-2']
        ]
        pull_request.title = u"Test"
        pull_request.description = u"Description"
        pull_request.author = UserModel().get_by_username(
            TEST_USER_ADMIN_LOGIN)
        Session().add(pull_request)
        Session().commit()
        pull_request_id = pull_request.pull_request_id

        # PR is created, now we simulate a force-push into target,
        # that drops a 2 last commits
        vcsrepo = target.scm_instance()
        vcsrepo.config.clear_section('hooks')
        vcsrepo.run_git_command(['reset', '--soft', 'HEAD~2'])

        # update PR
        self.app.post(
            route_path('pullrequest_update',
                repo_name=target.repo_name,
                pull_request_id=pull_request_id),
            params={'update_commits': 'true',
                    'csrf_token': csrf_token},
            status=200)

        response = self.app.get(route_path(
            'pullrequest_new',
            repo_name=target.repo_name))
        assert response.status_int == 200
        response.mustcontain('Pull request updated to')
        response.mustcontain('with 0 added, 0 removed commits.')

    def test_update_of_ancestor_reference(self, backend, csrf_token):
        commits = [
            {'message': 'ancestor'},
            {'message': 'change'},
            {'message': 'change-2'},
            {'message': 'ancestor-new', 'parents': ['ancestor']},
            {'message': 'change-rebased'},
        ]
        commit_ids = backend.create_master_repo(commits)
        target = backend.create_repo(heads=['ancestor'])
        source = backend.create_repo(heads=['change'])

        # create pr from a in source to A in target
        pull_request = PullRequest()
        pull_request.source_repo = source
        # TODO: johbo: Make sure that we write the source ref this way!
        pull_request.source_ref = 'branch:{branch}:{commit_id}'.format(
            branch=backend.default_branch_name,
            commit_id=commit_ids['change'])
        pull_request.target_repo = target
        # TODO: johbo: Target ref should be branch based, since tip can jump
        # from branch to branch
        pull_request.target_ref = 'branch:{branch}:{commit_id}'.format(
            branch=backend.default_branch_name,
            commit_id=commit_ids['ancestor'])
        pull_request.revisions = [commit_ids['change']]
        pull_request.title = u"Test"
        pull_request.description = u"Description"
        pull_request.author = UserModel().get_by_username(
            TEST_USER_ADMIN_LOGIN)
        Session().add(pull_request)
        Session().commit()
        pull_request_id = pull_request.pull_request_id

        # target has ancestor - ancestor-new
        # source has ancestor - ancestor-new - change-rebased
        backend.pull_heads(target, heads=['ancestor-new'])
        backend.pull_heads(source, heads=['change-rebased'])

        # update PR
        self.app.post(
            route_path('pullrequest_update',
                repo_name=target.repo_name,
                pull_request_id=pull_request_id),
            params={'update_commits': 'true',
                    'csrf_token': csrf_token},
            status=200)

        # Expect the target reference to be updated correctly
        pull_request = PullRequest.get(pull_request_id)
        assert pull_request.revisions == [commit_ids['change-rebased']]
        expected_target_ref = 'branch:{branch}:{commit_id}'.format(
            branch=backend.default_branch_name,
            commit_id=commit_ids['ancestor-new'])
        assert pull_request.target_ref == expected_target_ref

    def test_remove_pull_request_branch(self, backend_git, csrf_token):
        branch_name = 'development'
        commits = [
            {'message': 'initial-commit'},
            {'message': 'old-feature'},
            {'message': 'new-feature', 'branch': branch_name},
        ]
        repo = backend_git.create_repo(commits)
        commit_ids = backend_git.commit_ids

        pull_request = PullRequest()
        pull_request.source_repo = repo
        pull_request.target_repo = repo
        pull_request.source_ref = 'branch:{branch}:{commit_id}'.format(
            branch=branch_name, commit_id=commit_ids['new-feature'])
        pull_request.target_ref = 'branch:{branch}:{commit_id}'.format(
            branch=backend_git.default_branch_name,
            commit_id=commit_ids['old-feature'])
        pull_request.revisions = [commit_ids['new-feature']]
        pull_request.title = u"Test"
        pull_request.description = u"Description"
        pull_request.author = UserModel().get_by_username(
            TEST_USER_ADMIN_LOGIN)
        Session().add(pull_request)
        Session().commit()

        vcs = repo.scm_instance()
        vcs.remove_ref('refs/heads/{}'.format(branch_name))

        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=repo.repo_name,
            pull_request_id=pull_request.pull_request_id))

        assert response.status_int == 200
        assert_response = AssertResponse(response)
        assert_response.element_contains(
            '#changeset_compare_view_content .alert strong',
            'Missing commits')
        assert_response.element_contains(
            '#changeset_compare_view_content .alert',
            'This pull request cannot be displayed, because one or more'
            ' commits no longer exist in the source repository.')

    def test_strip_commits_from_pull_request(
            self, backend, pr_util, csrf_token):
        commits = [
            {'message': 'initial-commit'},
            {'message': 'old-feature'},
            {'message': 'new-feature', 'parents': ['initial-commit']},
        ]
        pull_request = pr_util.create_pull_request(
            commits, target_head='initial-commit', source_head='new-feature',
            revisions=['new-feature'])

        vcs = pr_util.source_repository.scm_instance()
        if backend.alias == 'git':
            vcs.strip(pr_util.commit_ids['new-feature'], branch_name='master')
        else:
            vcs.strip(pr_util.commit_ids['new-feature'])

        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=pr_util.target_repository.repo_name,
            pull_request_id=pull_request.pull_request_id))

        assert response.status_int == 200
        assert_response = AssertResponse(response)
        assert_response.element_contains(
            '#changeset_compare_view_content .alert strong',
            'Missing commits')
        assert_response.element_contains(
            '#changeset_compare_view_content .alert',
            'This pull request cannot be displayed, because one or more'
            ' commits no longer exist in the source repository.')
        assert_response.element_contains(
            '#update_commits',
            'Update commits')

    def test_strip_commits_and_update(
            self, backend, pr_util, csrf_token):
        commits = [
            {'message': 'initial-commit'},
            {'message': 'old-feature'},
            {'message': 'new-feature', 'parents': ['old-feature']},
        ]
        pull_request = pr_util.create_pull_request(
            commits, target_head='old-feature', source_head='new-feature',
            revisions=['new-feature'], mergeable=True)

        vcs = pr_util.source_repository.scm_instance()
        if backend.alias == 'git':
            vcs.strip(pr_util.commit_ids['new-feature'], branch_name='master')
        else:
            vcs.strip(pr_util.commit_ids['new-feature'])

        response = self.app.post(
            route_path('pullrequest_update',
                repo_name=pull_request.target_repo.repo_name,
                pull_request_id=pull_request.pull_request_id),
            params={'update_commits': 'true',
                    'csrf_token': csrf_token})

        assert response.status_int == 200
        assert response.body == 'true'

        # Make sure that after update, it won't raise 500 errors
        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=pr_util.target_repository.repo_name,
            pull_request_id=pull_request.pull_request_id))

        assert response.status_int == 200
        assert_response = AssertResponse(response)
        assert_response.element_contains(
            '#changeset_compare_view_content .alert strong',
            'Missing commits')

    def test_branch_is_a_link(self, pr_util):
        pull_request = pr_util.create_pull_request()
        pull_request.source_ref = 'branch:origin:1234567890abcdef'
        pull_request.target_ref = 'branch:target:abcdef1234567890'
        Session().add(pull_request)
        Session().commit()

        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id))
        assert response.status_int == 200
        assert_response = AssertResponse(response)

        origin = assert_response.get_element('.pr-origininfo .tag')
        origin_children = origin.getchildren()
        assert len(origin_children) == 1
        target = assert_response.get_element('.pr-targetinfo .tag')
        target_children = target.getchildren()
        assert len(target_children) == 1

        expected_origin_link = route_path(
            'repo_changelog',
            repo_name=pull_request.source_repo.scm_instance().name,
            params=dict(branch='origin'))
        expected_target_link = route_path(
            'repo_changelog',
            repo_name=pull_request.target_repo.scm_instance().name,
            params=dict(branch='target'))
        assert origin_children[0].attrib['href'] == expected_origin_link
        assert origin_children[0].text == 'branch: origin'
        assert target_children[0].attrib['href'] == expected_target_link
        assert target_children[0].text == 'branch: target'

    def test_bookmark_is_not_a_link(self, pr_util):
        pull_request = pr_util.create_pull_request()
        pull_request.source_ref = 'bookmark:origin:1234567890abcdef'
        pull_request.target_ref = 'bookmark:target:abcdef1234567890'
        Session().add(pull_request)
        Session().commit()

        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id))
        assert response.status_int == 200
        assert_response = AssertResponse(response)

        origin = assert_response.get_element('.pr-origininfo .tag')
        assert origin.text.strip() == 'bookmark: origin'
        assert origin.getchildren() == []

        target = assert_response.get_element('.pr-targetinfo .tag')
        assert target.text.strip() == 'bookmark: target'
        assert target.getchildren() == []

    def test_tag_is_not_a_link(self, pr_util):
        pull_request = pr_util.create_pull_request()
        pull_request.source_ref = 'tag:origin:1234567890abcdef'
        pull_request.target_ref = 'tag:target:abcdef1234567890'
        Session().add(pull_request)
        Session().commit()

        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id))
        assert response.status_int == 200
        assert_response = AssertResponse(response)

        origin = assert_response.get_element('.pr-origininfo .tag')
        assert origin.text.strip() == 'tag: origin'
        assert origin.getchildren() == []

        target = assert_response.get_element('.pr-targetinfo .tag')
        assert target.text.strip() == 'tag: target'
        assert target.getchildren() == []

    @pytest.mark.parametrize('mergeable', [True, False])
    def test_shadow_repository_link(
            self, mergeable, pr_util, http_host_only_stub):
        """
        Check that the pull request summary page displays a link to the shadow
        repository if the pull request is mergeable. If it is not mergeable
        the link should not be displayed.
        """
        pull_request = pr_util.create_pull_request(
            mergeable=mergeable, enable_notifications=False)
        target_repo = pull_request.target_repo.scm_instance()
        pr_id = pull_request.pull_request_id
        shadow_url = '{host}/{repo}/pull-request/{pr_id}/repository'.format(
            host=http_host_only_stub, repo=target_repo.name, pr_id=pr_id)

        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=target_repo.name,
            pull_request_id=pr_id))

        assertr = AssertResponse(response)
        if mergeable:
            assertr.element_value_contains('input.pr-mergeinfo', shadow_url)
            assertr.element_value_contains('input.pr-mergeinfo ', 'pr-merge')
        else:
            assertr.no_element_exists('.pr-mergeinfo')


@pytest.mark.usefixtures('app')
@pytest.mark.backends("git", "hg")
class TestPullrequestsControllerDelete(object):
    def test_pull_request_delete_button_permissions_admin(
            self, autologin_user, user_admin, pr_util):
        pull_request = pr_util.create_pull_request(
            author=user_admin.username, enable_notifications=False)

        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id))

        response.mustcontain('id="delete_pullrequest"')
        response.mustcontain('Confirm to delete this pull request')

    def test_pull_request_delete_button_permissions_owner(
            self, autologin_regular_user, user_regular, pr_util):
        pull_request = pr_util.create_pull_request(
            author=user_regular.username, enable_notifications=False)

        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id))

        response.mustcontain('id="delete_pullrequest"')
        response.mustcontain('Confirm to delete this pull request')

    def test_pull_request_delete_button_permissions_forbidden(
            self, autologin_regular_user, user_regular, user_admin, pr_util):
        pull_request = pr_util.create_pull_request(
            author=user_admin.username, enable_notifications=False)

        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id))
        response.mustcontain(no=['id="delete_pullrequest"'])
        response.mustcontain(no=['Confirm to delete this pull request'])

    def test_pull_request_delete_button_permissions_can_update_cannot_delete(
            self, autologin_regular_user, user_regular, user_admin, pr_util,
            user_util):

        pull_request = pr_util.create_pull_request(
            author=user_admin.username, enable_notifications=False)

        user_util.grant_user_permission_to_repo(
            pull_request.target_repo, user_regular,
            'repository.write')

        response = self.app.get(route_path(
            'pullrequest_show',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id))

        response.mustcontain('id="open_edit_pullrequest"')
        response.mustcontain('id="delete_pullrequest"')
        response.mustcontain(no=['Confirm to delete this pull request'])

    def test_delete_comment_returns_404_if_comment_does_not_exist(
            self, autologin_user, pr_util, user_admin, csrf_token, xhr_header):

        pull_request = pr_util.create_pull_request(
            author=user_admin.username, enable_notifications=False)

        self.app.post(
            route_path(
            'pullrequest_comment_delete',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id,
            comment_id=1024404),
            extra_environ=xhr_header,
            params={'csrf_token': csrf_token},
            status=404
        )

    def test_delete_comment(
            self, autologin_user, pr_util, user_admin, csrf_token, xhr_header):

        pull_request = pr_util.create_pull_request(
            author=user_admin.username, enable_notifications=False)
        comment = pr_util.create_comment()
        comment_id = comment.comment_id

        response = self.app.post(
            route_path(
            'pullrequest_comment_delete',
            repo_name=pull_request.target_repo.scm_instance().name,
            pull_request_id=pull_request.pull_request_id,
            comment_id=comment_id),
            extra_environ=xhr_header,
            params={'csrf_token': csrf_token},
            status=200
        )
        assert response.body == 'true'

    @pytest.mark.parametrize('url_type', [
        'pullrequest_new',
        'pullrequest_create',
        'pullrequest_update',
        'pullrequest_merge',
    ])
    def test_pull_request_is_forbidden_on_archived_repo(
            self, autologin_user, backend, xhr_header, user_util, url_type):

        # create a temporary repo
        source = user_util.create_repo(repo_type=backend.alias)
        repo_name = source.repo_name
        repo = Repository.get_by_repo_name(repo_name)
        repo.archived = True
        Session().commit()

        response = self.app.get(
            route_path(url_type, repo_name=repo_name, pull_request_id=1), status=302)

        msg = 'Action not supported for archived repository.'
        assert_session_flash(response, msg)


def assert_pull_request_status(pull_request, expected_status):
    status = ChangesetStatusModel().calculated_review_status(
        pull_request=pull_request)
    assert status == expected_status


@pytest.mark.parametrize('route', ['pullrequest_new', 'pullrequest_create'])
@pytest.mark.usefixtures("autologin_user")
def test_forbidde_to_repo_summary_for_svn_repositories(backend_svn, app, route):
    response = app.get(
        route_path(route, repo_name=backend_svn.repo_name), status=404)

