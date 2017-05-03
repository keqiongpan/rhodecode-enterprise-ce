import collections

import pytest

from rhodecode.lib.utils import PartialRenderer
from rhodecode.lib.utils2 import AttributeDict
from rhodecode.model.notification import EmailNotificationModel


def test_get_template_obj(pylonsapp):
    template = EmailNotificationModel().get_renderer(
        EmailNotificationModel.TYPE_TEST)
    assert isinstance(template, PartialRenderer)


def test_render_email(pylonsapp):
    kwargs = {}
    subject, headers, body, body_plaintext = EmailNotificationModel().render_email(
        EmailNotificationModel.TYPE_TEST, **kwargs)

    # subject
    assert subject == 'Test "Subject" hello "world"'

    # headers
    assert headers == 'X=Y'

    # body plaintext
    assert body_plaintext == 'Email Plaintext Body'

    # body
    assert 'This is a notification ' \
           'from RhodeCode. http://test.example.com:80/' in body
    assert 'Email Body' in body


def test_render_pr_email(pylonsapp, user_admin):

    ref = collections.namedtuple('Ref',
        'name, type')(
        'fxies123', 'book'
        )

    pr = collections.namedtuple('PullRequest',
        'pull_request_id, title, description, source_ref_parts, source_ref_name, target_ref_parts, target_ref_name')(
        200, 'Example Pull Request', 'Desc of PR', ref, 'bookmark', ref, 'Branch')

    source_repo = target_repo = collections.namedtuple('Repo',
        'type, repo_name')(
        'hg', 'pull_request_1')

    kwargs = {
        'user': '<marcin@rhodecode.com> Marcin Kuzminski',
        'pull_request': pr,
        'pull_request_commits': [],

        'pull_request_target_repo': target_repo,
        'pull_request_target_repo_url': 'x',

        'pull_request_source_repo': source_repo,
        'pull_request_source_repo_url': 'x',

        'pull_request_url': 'http://localhost/pr1',
    }

    subject, headers, body, body_plaintext = EmailNotificationModel().render_email(
        EmailNotificationModel.TYPE_PULL_REQUEST, **kwargs)

    # subject
    assert subject == 'Marcin Kuzminski wants you to review pull request #200: "Example Pull Request"'


@pytest.mark.parametrize('mention', [
    True,
    False
])
@pytest.mark.parametrize('email_type', [
    EmailNotificationModel.TYPE_COMMIT_COMMENT,
    EmailNotificationModel.TYPE_PULL_REQUEST_COMMENT
])
def test_render_comment_subject_no_newlines(pylonsapp, mention, email_type):
    ref = collections.namedtuple('Ref',
        'name, type')(
        'fxies123', 'book'
        )

    pr = collections.namedtuple('PullRequest',
        'pull_request_id, title, description, source_ref_parts, source_ref_name, target_ref_parts, target_ref_name')(
        200, 'Example Pull Request', 'Desc of PR', ref, 'bookmark', ref, 'Branch')

    source_repo = target_repo = collections.namedtuple('Repo',
        'type, repo_name')(
        'hg', 'pull_request_1')

    kwargs = {
        'user': '<marcin@rhodecode.com> Marcin Kuzminski',
        'commit': AttributeDict(raw_id='a'*40, message='Commit message'),
        'status_change': 'approved',
        'commit_target_repo': AttributeDict(),
        'repo_name': 'test-repo',
        'comment_file': 'test-file.py',
        'comment_line': 'n100',
        'comment_type': 'note',
        'commit_comment_url': 'http://comment-url',
        'instance_url': 'http://rc-instance',
        'comment_body': 'hello world',
        'mention': mention,

        'pr_comment_url': 'http://comment-url',
        'pr_source_repo': AttributeDict(repo_name='foobar'),
        'pr_source_repo_url': 'http://soirce-repo/url',
        'pull_request': pr,
        'pull_request_commits': [],

        'pull_request_target_repo': target_repo,
        'pull_request_target_repo_url': 'x',

        'pull_request_source_repo': source_repo,
        'pull_request_source_repo_url': 'x',
    }
    subject, headers, body, body_plaintext = EmailNotificationModel().render_email(
        email_type, **kwargs)

    assert '\n' not in subject
