# -*- coding: utf-8 -*-

# Copyright (C) 2010-2017 RhodeCode GmbH
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

from rhodecode.model.db import (
    ChangesetComment, Notification, UserNotification)
from rhodecode.model.meta import Session
from rhodecode.lib import helpers as h


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'repo_commit': '/{repo_name}/changeset/{commit_id}',
        'repo_commit_comment_create': '/{repo_name}/changeset/{commit_id}/comment/create',
        'repo_commit_comment_preview': '/{repo_name}/changeset/{commit_id}/comment/preview',
        'repo_commit_comment_delete': '/{repo_name}/changeset/{commit_id}/comment/{comment_id}/delete',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.backends("git", "hg", "svn")
class TestRepoCommitCommentsView(TestController):

    @pytest.fixture(autouse=True)
    def prepare(self, request, pylonsapp):
        for x in ChangesetComment.query().all():
            Session().delete(x)
        Session().commit()

        for x in Notification.query().all():
            Session().delete(x)
        Session().commit()

        request.addfinalizer(self.cleanup)

    def cleanup(self):
        for x in ChangesetComment.query().all():
            Session().delete(x)
        Session().commit()

        for x in Notification.query().all():
            Session().delete(x)
        Session().commit()

    @pytest.mark.parametrize('comment_type', ChangesetComment.COMMENT_TYPES)
    def test_create(self, comment_type, backend):
        self.log_user()
        commit = backend.repo.get_commit('300')
        commit_id = commit.raw_id
        text = u'CommentOnCommit'

        params = {'text': text, 'csrf_token': self.csrf_token,
                  'comment_type': comment_type}
        self.app.post(
            route_path('repo_commit_comment_create',
                       repo_name=backend.repo_name, commit_id=commit_id),
            params=params)

        response = self.app.get(
            route_path('repo_commit',
                       repo_name=backend.repo_name, commit_id=commit_id))

        # test DB
        assert ChangesetComment.query().count() == 1
        assert_comment_links(response, ChangesetComment.query().count(), 0)

        assert Notification.query().count() == 1
        assert ChangesetComment.query().count() == 1

        notification = Notification.query().all()[0]

        comment_id = ChangesetComment.query().first().comment_id
        assert notification.type_ == Notification.TYPE_CHANGESET_COMMENT

        sbj = 'left {0} on commit `{1}` in the {2} repository'.format(
            comment_type, h.show_id(commit), backend.repo_name)
        assert sbj in notification.subject

        lnk = (u'/{0}/changeset/{1}#comment-{2}'.format(
            backend.repo_name, commit_id, comment_id))
        assert lnk in notification.body

    @pytest.mark.parametrize('comment_type', ChangesetComment.COMMENT_TYPES)
    def test_create_inline(self, comment_type, backend):
        self.log_user()
        commit = backend.repo.get_commit('300')
        commit_id = commit.raw_id
        text = u'CommentOnCommit'
        f_path = 'vcs/web/simplevcs/views/repository.py'
        line = 'n1'

        params = {'text': text, 'f_path': f_path, 'line': line,
                  'comment_type': comment_type,
                  'csrf_token': self.csrf_token}

        self.app.post(
            route_path('repo_commit_comment_create',
                       repo_name=backend.repo_name, commit_id=commit_id),
            params=params)

        response = self.app.get(
            route_path('repo_commit',
                       repo_name=backend.repo_name, commit_id=commit_id))

        # test DB
        assert ChangesetComment.query().count() == 1
        assert_comment_links(response, 0, ChangesetComment.query().count())

        if backend.alias == 'svn':
            response.mustcontain(
                '''data-f-path="vcs/commands/summary.py" '''
                '''id="a_c--ad05457a43f8"'''
            )
        else:
            response.mustcontain(
                '''data-f-path="vcs/backends/hg.py" '''
                '''id="a_c--9c390eb52cd6"'''
            )

        assert Notification.query().count() == 1
        assert ChangesetComment.query().count() == 1

        notification = Notification.query().all()[0]
        comment = ChangesetComment.query().first()
        assert notification.type_ == Notification.TYPE_CHANGESET_COMMENT

        assert comment.revision == commit_id
        sbj = 'left {comment_type} on commit `{commit}` ' \
              '(file: `{f_path}`) in the {repo} repository'.format(
            commit=h.show_id(commit),
            f_path=f_path, line=line, repo=backend.repo_name,
            comment_type=comment_type)
        assert sbj in notification.subject

        lnk = (u'/{0}/changeset/{1}#comment-{2}'.format(
            backend.repo_name, commit_id, comment.comment_id))
        assert lnk in notification.body
        assert 'on line n1' in notification.body

    def test_create_with_mention(self, backend):
        self.log_user()

        commit_id = backend.repo.get_commit('300').raw_id
        text = u'@test_regular check CommentOnCommit'

        params = {'text': text, 'csrf_token': self.csrf_token}
        self.app.post(
            route_path('repo_commit_comment_create',
                       repo_name=backend.repo_name, commit_id=commit_id),
            params=params)

        response = self.app.get(
            route_path('repo_commit',
                       repo_name=backend.repo_name, commit_id=commit_id))
        # test DB
        assert ChangesetComment.query().count() == 1
        assert_comment_links(response, ChangesetComment.query().count(), 0)

        notification = Notification.query().one()

        assert len(notification.recipients) == 2
        users = [x.username for x in notification.recipients]

        # test_regular gets notification by @mention
        assert sorted(users) == [u'test_admin', u'test_regular']

    def test_create_with_status_change(self, backend):
        self.log_user()
        commit = backend.repo.get_commit('300')
        commit_id = commit.raw_id
        text = u'CommentOnCommit'
        f_path = 'vcs/web/simplevcs/views/repository.py'
        line = 'n1'

        params = {'text': text, 'changeset_status': 'approved',
                  'csrf_token': self.csrf_token}

        self.app.post(
            route_path(
                'repo_commit_comment_create',
                repo_name=backend.repo_name, commit_id=commit_id),
            params=params)

        response = self.app.get(
            route_path('repo_commit',
                       repo_name=backend.repo_name, commit_id=commit_id))

        # test DB
        assert ChangesetComment.query().count() == 1
        assert_comment_links(response, ChangesetComment.query().count(), 0)

        assert Notification.query().count() == 1
        assert ChangesetComment.query().count() == 1

        notification = Notification.query().all()[0]

        comment_id = ChangesetComment.query().first().comment_id
        assert notification.type_ == Notification.TYPE_CHANGESET_COMMENT

        sbj = 'left note on commit `{0}` (status: Approved) ' \
              'in the {1} repository'.format(
            h.show_id(commit), backend.repo_name)
        assert sbj in notification.subject

        lnk = (u'/{0}/changeset/{1}#comment-{2}'.format(
            backend.repo_name, commit_id, comment_id))
        assert lnk in notification.body

    def test_delete(self, backend):
        self.log_user()
        commit_id = backend.repo.get_commit('300').raw_id
        text = u'CommentOnCommit'

        params = {'text': text, 'csrf_token': self.csrf_token}
        self.app.post(
            route_path(
                'repo_commit_comment_create',
                repo_name=backend.repo_name, commit_id=commit_id),
            params=params)

        comments = ChangesetComment.query().all()
        assert len(comments) == 1
        comment_id = comments[0].comment_id

        self.app.post(
            route_path('repo_commit_comment_delete',
                       repo_name=backend.repo_name,
                       commit_id=commit_id,
                       comment_id=comment_id),
            params={'csrf_token': self.csrf_token})

        comments = ChangesetComment.query().all()
        assert len(comments) == 0

        response = self.app.get(
            route_path('repo_commit',
                       repo_name=backend.repo_name, commit_id=commit_id))
        assert_comment_links(response, 0, 0)

    @pytest.mark.parametrize('renderer, input, output', [
        ('rst', 'plain text', '<p>plain text</p>'),
        ('rst', 'header\n======', '<h1 class="title">header</h1>'),
        ('rst', '*italics*', '<em>italics</em>'),
        ('rst', '**bold**', '<strong>bold</strong>'),
        ('markdown', 'plain text', '<p>plain text</p>'),
        ('markdown', '# header', '<h1>header</h1>'),
        ('markdown', '*italics*', '<em>italics</em>'),
        ('markdown', '**bold**', '<strong>bold</strong>'),
    ], ids=['rst-plain', 'rst-header', 'rst-italics', 'rst-bold', 'md-plain',
            'md-header', 'md-italics', 'md-bold', ])
    def test_preview(self, renderer, input, output, backend, xhr_header):
        self.log_user()
        params = {
            'renderer': renderer,
            'text': input,
            'csrf_token': self.csrf_token
        }
        commit_id = '0' * 16  # fake this for tests
        response = self.app.post(
            route_path('repo_commit_comment_preview',
                        repo_name=backend.repo_name, commit_id=commit_id,),
            params=params,
            extra_environ=xhr_header)

        response.mustcontain(output)


def assert_comment_links(response, comments, inline_comments):
    if comments == 1:
        comments_text = "%d Commit comment" % comments
    else:
        comments_text = "%d Commit comments" % comments

    if inline_comments == 1:
        inline_comments_text = "%d Inline Comment" % inline_comments
    else:
        inline_comments_text = "%d Inline Comments" % inline_comments

    if comments:
        response.mustcontain('<a href="#comments">%s</a>,' % comments_text)
    else:
        response.mustcontain(comments_text)

    if inline_comments:
        response.mustcontain(
            'id="inline-comments-counter">%s</' % inline_comments_text)
    else:
        response.mustcontain(inline_comments_text)
