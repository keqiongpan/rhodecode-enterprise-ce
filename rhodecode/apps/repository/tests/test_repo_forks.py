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

from rhodecode.tests import TestController, assert_session_flash, HG_FORK, GIT_FORK

from rhodecode.tests.fixture import Fixture
from rhodecode.lib import helpers as h

from rhodecode.model.db import Repository
from rhodecode.model.repo import RepoModel
from rhodecode.model.user import UserModel
from rhodecode.model.meta import Session

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'repo_summary': '/{repo_name}',
        'repo_creating_check': '/{repo_name}/repo_creating_check',
        'repo_fork_new': '/{repo_name}/fork',
        'repo_fork_create': '/{repo_name}/fork/create',
        'repo_forks_show_all': '/{repo_name}/forks',
        'repo_forks_data': '/{repo_name}/forks/data',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


FORK_NAME = {
    'hg': HG_FORK,
    'git': GIT_FORK
}


@pytest.mark.skip_backends('svn')
class TestRepoForkViewTests(TestController):

    def test_show_forks(self, backend, xhr_header):
        self.log_user()
        response = self.app.get(
            route_path('repo_forks_data', repo_name=backend.repo_name),
            extra_environ=xhr_header)

        assert response.json == {u'data': [], u'draw': None,
                                 u'recordsFiltered': 0, u'recordsTotal': 0}

    def test_no_permissions_to_fork_page(self, backend, user_util):
        user = user_util.create_user(password='qweqwe')
        user_id = user.user_id
        self.log_user(user.username, 'qweqwe')

        user_model = UserModel()
        user_model.revoke_perm(user_id, 'hg.fork.repository')
        user_model.grant_perm(user_id, 'hg.fork.none')
        u = UserModel().get(user_id)
        u.inherit_default_permissions = False
        Session().commit()
        # try create a fork
        self.app.get(
            route_path('repo_fork_new', repo_name=backend.repo_name),
            status=404)

    def test_no_permissions_to_fork_submit(self, backend, csrf_token, user_util):
        user = user_util.create_user(password='qweqwe')
        user_id = user.user_id
        self.log_user(user.username, 'qweqwe')

        user_model = UserModel()
        user_model.revoke_perm(user_id, 'hg.fork.repository')
        user_model.grant_perm(user_id, 'hg.fork.none')
        u = UserModel().get(user_id)
        u.inherit_default_permissions = False
        Session().commit()
        # try create a fork
        self.app.post(
            route_path('repo_fork_create', repo_name=backend.repo_name),
            {'csrf_token': csrf_token},
            status=404)

    def test_fork_missing_data(self, autologin_user, backend, csrf_token):
        # try create a fork
        response = self.app.post(
            route_path('repo_fork_create', repo_name=backend.repo_name),
            {'csrf_token': csrf_token},
            status=200)
        # test if html fill works fine
        response.mustcontain('Missing value')

    def test_create_fork_page(self, autologin_user, backend):
        self.app.get(
            route_path('repo_fork_new', repo_name=backend.repo_name),
            status=200)

    def test_create_and_show_fork(
            self, autologin_user, backend, csrf_token, xhr_header):

        # create a fork
        fork_name = FORK_NAME[backend.alias]
        description = 'fork of vcs test'
        repo_name = backend.repo_name
        source_repo = Repository.get_by_repo_name(repo_name)
        creation_args = {
            'repo_name': fork_name,
            'repo_group': '',
            'fork_parent_id': source_repo.repo_id,
            'repo_type': backend.alias,
            'description': description,
            'private': 'False',
            'csrf_token': csrf_token,
        }

        self.app.post(
            route_path('repo_fork_create', repo_name=repo_name), creation_args)

        response = self.app.get(
            route_path('repo_forks_data', repo_name=repo_name),
            extra_environ=xhr_header)

        assert response.json['data'][0]['fork_name'] == \
            """<a href="/%s">%s</a>""" % (fork_name, fork_name)

        # remove this fork
        fixture.destroy_repo(fork_name)

    def test_fork_create(self, autologin_user, backend, csrf_token):
        fork_name = FORK_NAME[backend.alias]
        description = 'fork of vcs test'
        repo_name = backend.repo_name
        source_repo = Repository.get_by_repo_name(repo_name)
        creation_args = {
            'repo_name': fork_name,
            'repo_group': '',
            'fork_parent_id': source_repo.repo_id,
            'repo_type': backend.alias,
            'description': description,
            'private': 'False',
            'csrf_token': csrf_token,
        }
        self.app.post(
            route_path('repo_fork_create', repo_name=repo_name), creation_args)
        repo = Repository.get_by_repo_name(FORK_NAME[backend.alias])
        assert repo.fork.repo_name == backend.repo_name

        # run the check page that triggers the flash message
        response = self.app.get(
            route_path('repo_creating_check', repo_name=fork_name))
        # test if we have a message that fork is ok
        assert_session_flash(response,
                'Forked repository %s as <a href="/%s">%s</a>' % (
                                 repo_name, fork_name, fork_name))

        # test if the fork was created in the database
        fork_repo = Session().query(Repository)\
            .filter(Repository.repo_name == fork_name).one()

        assert fork_repo.repo_name == fork_name
        assert fork_repo.fork.repo_name == repo_name

        # test if the repository is visible in the list ?
        response = self.app.get(
            h.route_path('repo_summary', repo_name=fork_name))
        response.mustcontain(fork_name)
        response.mustcontain(backend.alias)
        response.mustcontain('Fork of')
        response.mustcontain('<a href="/%s">%s</a>' % (repo_name, repo_name))

    def test_fork_create_into_group(self, autologin_user, backend, csrf_token):
        group = fixture.create_repo_group('vc')
        group_id = group.group_id
        fork_name = FORK_NAME[backend.alias]
        fork_name_full = 'vc/%s' % fork_name
        description = 'fork of vcs test'
        repo_name = backend.repo_name
        source_repo = Repository.get_by_repo_name(repo_name)
        creation_args = {
            'repo_name': fork_name,
            'repo_group': group_id,
            'fork_parent_id': source_repo.repo_id,
            'repo_type': backend.alias,
            'description': description,
            'private': 'False',
            'csrf_token': csrf_token,
        }
        self.app.post(
            route_path('repo_fork_create', repo_name=repo_name), creation_args)
        repo = Repository.get_by_repo_name(fork_name_full)
        assert repo.fork.repo_name == backend.repo_name

        # run the check page that triggers the flash message
        response = self.app.get(
            route_path('repo_creating_check', repo_name=fork_name_full))
        # test if we have a message that fork is ok
        assert_session_flash(response,
                             'Forked repository %s as <a href="/%s">%s</a>' % (
                                 repo_name, fork_name_full, fork_name_full))

        # test if the fork was created in the database
        fork_repo = Session().query(Repository)\
            .filter(Repository.repo_name == fork_name_full).one()

        assert fork_repo.repo_name == fork_name_full
        assert fork_repo.fork.repo_name == repo_name

        # test if the repository is visible in the list ?
        response = self.app.get(
            h.route_path('repo_summary', repo_name=fork_name_full))
        response.mustcontain(fork_name_full)
        response.mustcontain(backend.alias)

        response.mustcontain('Fork of')
        response.mustcontain('<a href="/%s">%s</a>' % (repo_name, repo_name))

        fixture.destroy_repo(fork_name_full)
        fixture.destroy_repo_group(group_id)

    def test_fork_read_permission(self, backend, xhr_header, user_util):
        user = user_util.create_user(password='qweqwe')
        user_id = user.user_id
        self.log_user(user.username, 'qweqwe')

        # create a fake fork
        fork = user_util.create_repo(repo_type=backend.alias)
        source = user_util.create_repo(repo_type=backend.alias)
        repo_name = source.repo_name

        fork.fork_id = source.repo_id
        fork_name = fork.repo_name
        Session().commit()

        forks = Repository.query()\
            .filter(Repository.repo_type == backend.alias)\
            .filter(Repository.fork_id == source.repo_id).all()
        assert 1 == len(forks)

        # set read permissions for this
        RepoModel().grant_user_permission(
            repo=forks[0], user=user_id, perm='repository.read')
        Session().commit()

        response = self.app.get(
            route_path('repo_forks_data', repo_name=repo_name),
            extra_environ=xhr_header)

        assert response.json['data'][0]['fork_name'] == \
            """<a href="/%s">%s</a>""" % (fork_name, fork_name)

    def test_fork_none_permission(self, backend, xhr_header, user_util):
        user = user_util.create_user(password='qweqwe')
        user_id = user.user_id
        self.log_user(user.username, 'qweqwe')

        # create a fake fork
        fork = user_util.create_repo(repo_type=backend.alias)
        source = user_util.create_repo(repo_type=backend.alias)
        repo_name = source.repo_name

        fork.fork_id = source.repo_id

        Session().commit()

        forks = Repository.query()\
            .filter(Repository.repo_type == backend.alias)\
            .filter(Repository.fork_id == source.repo_id).all()
        assert 1 == len(forks)

        # set none
        RepoModel().grant_user_permission(
            repo=forks[0], user=user_id, perm='repository.none')
        Session().commit()

        # fork shouldn't be there
        response = self.app.get(
            route_path('repo_forks_data', repo_name=repo_name),
            extra_environ=xhr_header)

        assert response.json == {u'data': [], u'draw': None,
                                 u'recordsFiltered': 0, u'recordsTotal': 0}

    @pytest.mark.parametrize('url_type', [
        'repo_fork_new',
        'repo_fork_create'
    ])
    def test_fork_is_forbidden_on_archived_repo(self, backend, xhr_header, user_util, url_type):
        user = user_util.create_user(password='qweqwe')
        self.log_user(user.username, 'qweqwe')

        # create a temporary repo
        source = user_util.create_repo(repo_type=backend.alias)
        repo_name = source.repo_name
        repo = Repository.get_by_repo_name(repo_name)
        repo.archived = True
        Session().commit()

        response = self.app.get(
            route_path(url_type, repo_name=repo_name), status=302)

        msg = 'Action not supported for archived repository.'
        assert_session_flash(response, msg)


class TestSVNFork(TestController):
    @pytest.mark.parametrize('route_name', [
        'repo_fork_create', 'repo_fork_new'
    ])
    def test_fork_redirects(self, autologin_user, backend_svn, route_name):

        self.app.get(route_path(
            route_name, repo_name=backend_svn.repo_name),
            status=404)
