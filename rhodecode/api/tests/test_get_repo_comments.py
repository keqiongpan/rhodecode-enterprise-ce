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

from rhodecode.model.db import User, ChangesetComment
from rhodecode.model.meta import Session
from rhodecode.model.comment import CommentsModel
from rhodecode.api.tests.utils import (
    build_data, api_call, assert_error, assert_call_ok)


@pytest.fixture()
def make_repo_comments_factory(request):

    class Make(object):

        def make_comments(self, repo):
            user = User.get_first_super_admin()
            commit = repo.scm_instance()[0]

            commit_id = commit.raw_id
            file_0 = commit.affected_files[0]
            comments = []

            # general
            CommentsModel().create(
                text='General Comment', repo=repo, user=user, commit_id=commit_id,
                comment_type=ChangesetComment.COMMENT_TYPE_NOTE, send_email=False)

            # inline
            CommentsModel().create(
                text='Inline Comment', repo=repo, user=user, commit_id=commit_id,
                f_path=file_0, line_no='n1',
                comment_type=ChangesetComment.COMMENT_TYPE_NOTE, send_email=False)

            # todo
            CommentsModel().create(
                text='INLINE TODO Comment', repo=repo, user=user, commit_id=commit_id,
                f_path=file_0, line_no='n1',
                comment_type=ChangesetComment.COMMENT_TYPE_TODO, send_email=False)

            @request.addfinalizer
            def cleanup():
                for comment in comments:
                    Session().delete(comment)
    return Make()


@pytest.mark.usefixtures("testuser_api", "app")
class TestGetRepo(object):

    @pytest.mark.parametrize('filters, expected_count', [
        ({}, 3),
        ({'comment_type': ChangesetComment.COMMENT_TYPE_NOTE}, 2),
        ({'comment_type': ChangesetComment.COMMENT_TYPE_TODO}, 1),
        ({'commit_id': 'FILLED DYNAMIC'}, 3),
    ])
    def test_api_get_repo_comments(self, backend, user_util,
                                   make_repo_comments_factory, filters, expected_count):
        commits = [{'message': 'A'}, {'message': 'B'}]
        repo = backend.create_repo(commits=commits)
        make_repo_comments_factory.make_comments(repo)

        api_call_params = {'repoid': repo.repo_name,}
        api_call_params.update(filters)

        if 'commit_id' in api_call_params:
            commit = repo.scm_instance()[0]
            commit_id = commit.raw_id
            api_call_params['commit_id'] = commit_id

        id_, params = build_data(self.apikey, 'get_repo_comments', **api_call_params)
        response = api_call(self.app, params)
        result = assert_call_ok(id_, given=response.body)

        assert len(result) == expected_count

    def test_api_get_repo_comments_wrong_comment_type(
            self, make_repo_comments_factory, backend_hg):
        commits = [{'message': 'A'}, {'message': 'B'}]
        repo = backend_hg.create_repo(commits=commits)
        make_repo_comments_factory.make_comments(repo)

        api_call_params = {'repoid': repo.repo_name}
        api_call_params.update({'comment_type': 'bogus'})

        expected = 'comment_type must be one of `{}` got {}'.format(
                    ChangesetComment.COMMENT_TYPES, 'bogus')
        id_, params = build_data(self.apikey, 'get_repo_comments', **api_call_params)
        response = api_call(self.app, params)
        assert_error(id_, expected, given=response.body)
