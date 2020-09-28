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

from rhodecode.tests import TestController

from rhodecode.model.db import ChangesetComment, Notification
from rhodecode.model.meta import Session
from rhodecode.lib import helpers as h


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'repo_commit': '/{repo_name}/changeset/{commit_id}',
        'repo_commit_comment_create': '/{repo_name}/changeset/{commit_id}/comment/create',
        'repo_commit_comment_preview': '/{repo_name}/changeset/{commit_id}/comment/preview',
        'repo_commit_comment_delete': '/{repo_name}/changeset/{commit_id}/comment/{comment_id}/delete',
        'repo_commit_comment_edit': '/{repo_name}/changeset/{commit_id}/comment/{comment_id}/edit',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.backends("git", "hg", "svn")
class TestRepoCommitCommentsView(TestController):

    @pytest.fixture(autouse=True)
    def prepare(self, request, baseapp):
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

        author = notification.created_by_user.username_and_name
        sbj = '@{0} left a {1} on commit `{2}` in the `{3}` repository'.format(
            author, comment_type, h.show_id(commit), backend.repo_name)
        assert sbj == notification.subject

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
                '''data-anchor-id="c-300-ad05457a43f8"'''
            )
        if backend.alias == 'git':
            response.mustcontain(
                '''data-f-path="vcs/backends/hg.py" '''
                '''data-anchor-id="c-883e775e89ea-9c390eb52cd6"'''
            )

        if backend.alias == 'hg':
            response.mustcontain(
                '''data-f-path="vcs/backends/hg.py" '''
                '''data-anchor-id="c-e58d85a3973b-9c390eb52cd6"'''
            )

        assert Notification.query().count() == 1
        assert ChangesetComment.query().count() == 1

        notification = Notification.query().all()[0]
        comment = ChangesetComment.query().first()
        assert notification.type_ == Notification.TYPE_CHANGESET_COMMENT

        assert comment.revision == commit_id

        author = notification.created_by_user.username_and_name
        sbj = '@{0} left a {1} on file `{2}` in commit `{3}` in the `{4}` repository'.format(
            author, comment_type, f_path, h.show_id(commit), backend.repo_name)

        assert sbj == notification.subject

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

        author = notification.created_by_user.username_and_name
        sbj = '[status: Approved] @{0} left a note on commit `{1}` in the `{2}` repository'.format(
            author, h.show_id(commit), backend.repo_name)
        assert sbj == notification.subject

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

    def test_edit(self, backend):
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
        test_text = 'test_text'
        self.app.post(
            route_path(
                'repo_commit_comment_edit',
                repo_name=backend.repo_name,
                commit_id=commit_id,
                comment_id=comment_id,
            ),
            params={
                'csrf_token': self.csrf_token,
                'text': test_text,
                'version': '0',
            })

        text_form_db = ChangesetComment.query().filter(
            ChangesetComment.comment_id == comment_id).first().text
        assert test_text == text_form_db

    def test_edit_without_change(self, backend):
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

        response = self.app.post(
            route_path(
                'repo_commit_comment_edit',
                repo_name=backend.repo_name,
                commit_id=commit_id,
                comment_id=comment_id,
            ),
            params={
                'csrf_token': self.csrf_token,
                'text': text,
                'version': '0',
            },
            status=404,
        )
        assert response.status_int == 404

    def test_edit_try_edit_already_edited(self, backend):
        self.log_user()
        commit_id = backend.repo.get_commit('300').raw_id
        text = u'CommentOnCommit'

        params = {'text': text, 'csrf_token': self.csrf_token}
        self.app.post(
            route_path(
                'repo_commit_comment_create',
                repo_name=backend.repo_name, commit_id=commit_id
            ),
            params=params,
        )

        comments = ChangesetComment.query().all()
        assert len(comments) == 1
        comment_id = comments[0].comment_id
        test_text = 'test_text'
        self.app.post(
            route_path(
                'repo_commit_comment_edit',
                repo_name=backend.repo_name,
                commit_id=commit_id,
                comment_id=comment_id,
            ),
            params={
                'csrf_token': self.csrf_token,
                'text': test_text,
                'version': '0',
            }
        )
        test_text_v2 = 'test_v2'
        response = self.app.post(
            route_path(
                'repo_commit_comment_edit',
                repo_name=backend.repo_name,
                commit_id=commit_id,
                comment_id=comment_id,
            ),
            params={
                'csrf_token': self.csrf_token,
                'text': test_text_v2,
                'version': '0',
            },
            status=409,
        )
        assert response.status_int == 409

        text_form_db = ChangesetComment.query().filter(
            ChangesetComment.comment_id == comment_id).first().text

        assert test_text == text_form_db
        assert test_text_v2 != text_form_db

    def test_edit_forbidden_for_immutable_comments(self, backend):
        self.log_user()
        commit_id = backend.repo.get_commit('300').raw_id
        text = u'CommentOnCommit'

        params = {'text': text, 'csrf_token': self.csrf_token, 'version': '0'}
        self.app.post(
            route_path(
                'repo_commit_comment_create',
                repo_name=backend.repo_name,
                commit_id=commit_id,
            ),
            params=params
        )

        comments = ChangesetComment.query().all()
        assert len(comments) == 1
        comment_id = comments[0].comment_id

        comment = ChangesetComment.get(comment_id)
        comment.immutable_state = ChangesetComment.OP_IMMUTABLE
        Session().add(comment)
        Session().commit()

        response = self.app.post(
            route_path(
                'repo_commit_comment_edit',
                repo_name=backend.repo_name,
                commit_id=commit_id,
                comment_id=comment_id,
            ),
            params={
                'csrf_token': self.csrf_token,
                'text': 'test_text',
            },
            status=403,
        )
        assert response.status_int == 403

    def test_delete_forbidden_for_immutable_comments(self, backend):
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

        comment = ChangesetComment.get(comment_id)
        comment.immutable_state = ChangesetComment.OP_IMMUTABLE
        Session().add(comment)
        Session().commit()

        self.app.post(
            route_path('repo_commit_comment_delete',
                       repo_name=backend.repo_name,
                       commit_id=commit_id,
                       comment_id=comment_id),
            params={'csrf_token': self.csrf_token},
            status=403)

    @pytest.mark.parametrize('renderer, text_input, output', [
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
    def test_preview(self, renderer, text_input, output, backend, xhr_header):
        self.log_user()
        params = {
            'renderer': renderer,
            'text': text_input,
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
    response.mustcontain(
        '<span class="display-none" id="general-comments-count">{}</span>'.format(comments))
    response.mustcontain(
        '<span class="display-none" id="inline-comments-count">{}</span>'.format(inline_comments))



