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
import collections

from rhodecode.lib.partial_renderer import PyramidPartialRenderer
from rhodecode.lib.utils2 import AttributeDict
from rhodecode.model.db import User, PullRequestReviewers
from rhodecode.model.notification import EmailNotificationModel


@pytest.fixture()
def pr():
    def factory(ref):
        return collections.namedtuple(
            'PullRequest',
            'pull_request_id, title, title_safe, description, source_ref_parts, source_ref_name, target_ref_parts, target_ref_name')\
            (200, 'Example Pull Request', 'Example Pull Request', 'Desc of PR', ref, 'bookmark', ref, 'Branch')
    return factory


def test_get_template_obj(app, request_stub):
    template = EmailNotificationModel().get_renderer(
        EmailNotificationModel.TYPE_TEST, request_stub)
    assert isinstance(template, PyramidPartialRenderer)


def test_render_email(app, http_host_only_stub):
    kwargs = {}
    subject, body, body_plaintext = EmailNotificationModel().render_email(
        EmailNotificationModel.TYPE_TEST, **kwargs)

    # subject
    assert subject == 'Test "Subject" hello "world"'

    # body plaintext
    assert body_plaintext == 'Email Plaintext Body'

    # body
    notification_footer1 = 'This is a notification from RhodeCode.'
    notification_footer2 = 'http://{}/'.format(http_host_only_stub)
    assert notification_footer1 in body
    assert notification_footer2 in body
    assert 'Email Body' in body


@pytest.mark.parametrize('role', PullRequestReviewers.ROLES)
def test_render_pr_email(app, user_admin, role, pr):
    ref = collections.namedtuple(
        'Ref', 'name, type')('fxies123', 'book')
    pr = pr(ref)
    source_repo = target_repo = collections.namedtuple(
        'Repo', 'type, repo_name')('hg', 'pull_request_1')

    kwargs = {
        'user': User.get_first_super_admin(),
        'pull_request': pr,
        'pull_request_commits': [],

        'pull_request_target_repo': target_repo,
        'pull_request_target_repo_url': 'x',

        'pull_request_source_repo': source_repo,
        'pull_request_source_repo_url': 'x',

        'pull_request_url': 'http://localhost/pr1',
        'user_role': role,
    }

    subject, body, body_plaintext = EmailNotificationModel().render_email(
        EmailNotificationModel.TYPE_PULL_REQUEST, **kwargs)

    # subject
    if role == PullRequestReviewers.ROLE_REVIEWER:
        assert subject == '@test_admin (RhodeCode Admin) requested a pull request review. !200: "Example Pull Request"'
    elif role == PullRequestReviewers.ROLE_OBSERVER:
        assert subject == '@test_admin (RhodeCode Admin) added you as observer to pull request. !200: "Example Pull Request"'


def test_render_pr_update_email(app, user_admin, pr):
    ref = collections.namedtuple(
        'Ref', 'name, type')('fxies123', 'book')

    pr = pr(ref)

    source_repo = target_repo = collections.namedtuple(
        'Repo', 'type, repo_name')('hg', 'pull_request_1')

    commit_changes = AttributeDict({
        'added': ['aaaaaaabbbbb', 'cccccccddddddd'],
        'removed': ['eeeeeeeeeee'],
    })
    file_changes = AttributeDict({
        'added': ['a/file1.md', 'file2.py'],
        'modified': ['b/modified_file.rst'],
        'removed': ['.idea'],
    })

    kwargs = {
        'updating_user': User.get_first_super_admin(),

        'pull_request': pr,
        'pull_request_commits': [],

        'pull_request_target_repo': target_repo,
        'pull_request_target_repo_url': 'x',

        'pull_request_source_repo': source_repo,
        'pull_request_source_repo_url': 'x',

        'pull_request_url': 'http://localhost/pr1',

        'pr_comment_url': 'http://comment-url',
        'pr_comment_reply_url': 'http://comment-url#reply',
        'ancestor_commit_id': 'f39bd443',
        'added_commits': commit_changes.added,
        'removed_commits': commit_changes.removed,
        'changed_files': (file_changes.added + file_changes.modified + file_changes.removed),
        'added_files': file_changes.added,
        'modified_files': file_changes.modified,
        'removed_files': file_changes.removed,
    }

    subject, body, body_plaintext = EmailNotificationModel().render_email(
        EmailNotificationModel.TYPE_PULL_REQUEST_UPDATE, **kwargs)

    # subject
    assert subject == '@test_admin (RhodeCode Admin) updated pull request. !200: "Example Pull Request"'


@pytest.mark.parametrize('mention', [
    True,
    False
])
@pytest.mark.parametrize('email_type', [
    EmailNotificationModel.TYPE_COMMIT_COMMENT,
    EmailNotificationModel.TYPE_PULL_REQUEST_COMMENT
])
def test_render_comment_subject_no_newlines(app, mention, email_type, pr):
    ref = collections.namedtuple(
        'Ref', 'name, type')('fxies123', 'book')

    pr = pr(ref)

    source_repo = target_repo = collections.namedtuple(
        'Repo', 'type, repo_name')('hg', 'pull_request_1')

    kwargs = {
        'user': User.get_first_super_admin(),
        'commit': AttributeDict(raw_id='a'*40, message='Commit message'),
        'status_change': 'approved',
        'commit_target_repo_url': 'http://foo.example.com/#comment1',
        'repo_name': 'test-repo',
        'comment_file': 'test-file.py',
        'comment_line': 'n100',
        'comment_type': 'note',
        'comment_id': 2048,
        'commit_comment_url': 'http://comment-url',
        'commit_comment_reply_url': 'http://comment-url/#Reply',
        'instance_url': 'http://rc-instance',
        'comment_body': 'hello world',
        'mention': mention,

        'pr_comment_url': 'http://comment-url',
        'pr_comment_reply_url': 'http://comment-url/#Reply',
        'pull_request': pr,
        'pull_request_commits': [],

        'pull_request_target_repo': target_repo,
        'pull_request_target_repo_url': 'x',

        'pull_request_source_repo': source_repo,
        'pull_request_source_repo_url': 'x',

        'pull_request_url': 'http://code.rc.com/_pr/123'
    }
    subject, body, body_plaintext = EmailNotificationModel().render_email(email_type, **kwargs)

    assert '\n' not in subject
