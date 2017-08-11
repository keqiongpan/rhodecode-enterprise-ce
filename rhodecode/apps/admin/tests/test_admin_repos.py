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

import urllib

import mock
import pytest

from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.lib import auth
from rhodecode.lib.utils2 import safe_str
from rhodecode.lib import helpers as h
from rhodecode.model.db import (
    Repository, RepoGroup, UserRepoToPerm, User, Permission)
from rhodecode.model.meta import Session
from rhodecode.model.repo import RepoModel
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.user import UserModel
from rhodecode.tests import (
    login_user_session, assert_session_flash, TEST_USER_ADMIN_LOGIN,
    TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
from rhodecode.tests.fixture import Fixture, error_function
from rhodecode.tests.utils import AssertResponse, repo_on_filesystem

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'repos': ADMIN_PREFIX + '/repos',
        'repo_new': ADMIN_PREFIX + '/repos/new',
        'repo_create': ADMIN_PREFIX + '/repos/create',

        'repo_creating_check': '/{repo_name}/repo_creating_check',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


def _get_permission_for_user(user, repo):
    perm = UserRepoToPerm.query()\
        .filter(UserRepoToPerm.repository ==
                Repository.get_by_repo_name(repo))\
        .filter(UserRepoToPerm.user == User.get_by_username(user))\
        .all()
    return perm


@pytest.mark.usefixtures("app")
class TestAdminRepos(object):

    def test_repo_list(self, autologin_user, user_util):
        repo = user_util.create_repo()
        response = self.app.get(
            route_path('repos'), status=200)

        response.mustcontain(repo.repo_name)

    def test_create_page_restricted_to_single_backend(self, autologin_user, backend):
        with mock.patch('rhodecode.BACKENDS', {'git': 'git'}):
            response = self.app.get(route_path('repo_new'), status=200)
        assert_response = AssertResponse(response)
        element = assert_response.get_element('#repo_type')
        assert element.text_content() == '\ngit\n'

    def test_create_page_non_restricted_backends(self, autologin_user, backend):
        response = self.app.get(route_path('repo_new'), status=200)
        assert_response = AssertResponse(response)
        assert_response.element_contains('#repo_type', 'git')
        assert_response.element_contains('#repo_type', 'svn')
        assert_response.element_contains('#repo_type', 'hg')

    @pytest.mark.parametrize(
        "suffix", [u'', u'xxa'], ids=['', 'non-ascii'])
    def test_create(self, autologin_user, backend, suffix, csrf_token):
        repo_name_unicode = backend.new_repo_name(suffix=suffix)
        repo_name = repo_name_unicode.encode('utf8')
        description_unicode = u'description for newly created repo' + suffix
        description = description_unicode.encode('utf8')
        response = self.app.post(
            route_path('repo_create'),
            fixture._get_repo_create_params(
                repo_private=False,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_description=description,
                csrf_token=csrf_token),
            status=302)

        self.assert_repository_is_created_correctly(
            repo_name, description, backend)

    def test_create_numeric_name(self, autologin_user, backend, csrf_token):
        numeric_repo = '1234'
        repo_name = numeric_repo
        description = 'description for newly created repo' + numeric_repo
        self.app.post(
            route_path('repo_create'),
            fixture._get_repo_create_params(
                repo_private=False,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_description=description,
                csrf_token=csrf_token))

        self.assert_repository_is_created_correctly(
            repo_name, description, backend)

    @pytest.mark.parametrize("suffix", [u'', u'ąćę'], ids=['', 'non-ascii'])
    def test_create_in_group(
            self, autologin_user, backend, suffix, csrf_token):
        # create GROUP
        group_name = 'sometest_%s' % backend.alias
        gr = RepoGroupModel().create(group_name=group_name,
                                     group_description='test',
                                     owner=TEST_USER_ADMIN_LOGIN)
        Session().commit()

        repo_name = u'ingroup' + suffix
        repo_name_full = RepoGroup.url_sep().join(
            [group_name, repo_name])
        description = u'description for newly created repo'
        self.app.post(
            route_path('repo_create'),
            fixture._get_repo_create_params(
                repo_private=False,
                repo_name=safe_str(repo_name),
                repo_type=backend.alias,
                repo_description=description,
                repo_group=gr.group_id,
                csrf_token=csrf_token))

        # TODO: johbo: Cleanup work to fixture
        try:
            self.assert_repository_is_created_correctly(
                repo_name_full, description, backend)

            new_repo = RepoModel().get_by_repo_name(repo_name_full)
            inherited_perms = UserRepoToPerm.query().filter(
                UserRepoToPerm.repository_id == new_repo.repo_id).all()
            assert len(inherited_perms) == 1
        finally:
            RepoModel().delete(repo_name_full)
            RepoGroupModel().delete(group_name)
            Session().commit()

    def test_create_in_group_numeric_name(
            self, autologin_user, backend, csrf_token):
        # create GROUP
        group_name = 'sometest_%s' % backend.alias
        gr = RepoGroupModel().create(group_name=group_name,
                                     group_description='test',
                                     owner=TEST_USER_ADMIN_LOGIN)
        Session().commit()

        repo_name = '12345'
        repo_name_full = RepoGroup.url_sep().join([group_name, repo_name])
        description = 'description for newly created repo'
        self.app.post(
            route_path('repo_create'),
            fixture._get_repo_create_params(
                repo_private=False,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_description=description,
                repo_group=gr.group_id,
                csrf_token=csrf_token))

        # TODO: johbo: Cleanup work to fixture
        try:
            self.assert_repository_is_created_correctly(
                repo_name_full, description, backend)

            new_repo = RepoModel().get_by_repo_name(repo_name_full)
            inherited_perms = UserRepoToPerm.query()\
                .filter(UserRepoToPerm.repository_id == new_repo.repo_id).all()
            assert len(inherited_perms) == 1
        finally:
            RepoModel().delete(repo_name_full)
            RepoGroupModel().delete(group_name)
            Session().commit()

    def test_create_in_group_without_needed_permissions(self, backend):
        session = login_user_session(
            self.app, TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        csrf_token = auth.get_csrf_token(session)
        # revoke
        user_model = UserModel()
        # disable fork and create on default user
        user_model.revoke_perm(User.DEFAULT_USER, 'hg.create.repository')
        user_model.grant_perm(User.DEFAULT_USER, 'hg.create.none')
        user_model.revoke_perm(User.DEFAULT_USER, 'hg.fork.repository')
        user_model.grant_perm(User.DEFAULT_USER, 'hg.fork.none')

        # disable on regular user
        user_model.revoke_perm(TEST_USER_REGULAR_LOGIN, 'hg.create.repository')
        user_model.grant_perm(TEST_USER_REGULAR_LOGIN, 'hg.create.none')
        user_model.revoke_perm(TEST_USER_REGULAR_LOGIN, 'hg.fork.repository')
        user_model.grant_perm(TEST_USER_REGULAR_LOGIN, 'hg.fork.none')
        Session().commit()

        # create GROUP
        group_name = 'reg_sometest_%s' % backend.alias
        gr = RepoGroupModel().create(group_name=group_name,
                                     group_description='test',
                                     owner=TEST_USER_ADMIN_LOGIN)
        Session().commit()

        group_name_allowed = 'reg_sometest_allowed_%s' % backend.alias
        gr_allowed = RepoGroupModel().create(
            group_name=group_name_allowed,
            group_description='test',
            owner=TEST_USER_REGULAR_LOGIN)
        Session().commit()

        repo_name = 'ingroup'
        description = 'description for newly created repo'
        response = self.app.post(
            route_path('repo_create'),
            fixture._get_repo_create_params(
                repo_private=False,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_description=description,
                repo_group=gr.group_id,
                csrf_token=csrf_token))

        response.mustcontain('Invalid value')

        # user is allowed to create in this group
        repo_name = 'ingroup'
        repo_name_full = RepoGroup.url_sep().join(
            [group_name_allowed, repo_name])
        description = 'description for newly created repo'
        response = self.app.post(
            route_path('repo_create'),
            fixture._get_repo_create_params(
                repo_private=False,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_description=description,
                repo_group=gr_allowed.group_id,
                csrf_token=csrf_token))

        # TODO: johbo: Cleanup in pytest fixture
        try:
            self.assert_repository_is_created_correctly(
                repo_name_full, description, backend)

            new_repo = RepoModel().get_by_repo_name(repo_name_full)
            inherited_perms = UserRepoToPerm.query().filter(
                UserRepoToPerm.repository_id == new_repo.repo_id).all()
            assert len(inherited_perms) == 1

            assert repo_on_filesystem(repo_name_full)
        finally:
            RepoModel().delete(repo_name_full)
            RepoGroupModel().delete(group_name)
            RepoGroupModel().delete(group_name_allowed)
            Session().commit()

    def test_create_in_group_inherit_permissions(self, autologin_user, backend,
                                                 csrf_token):
        # create GROUP
        group_name = 'sometest_%s' % backend.alias
        gr = RepoGroupModel().create(group_name=group_name,
                                     group_description='test',
                                     owner=TEST_USER_ADMIN_LOGIN)
        perm = Permission.get_by_key('repository.write')
        RepoGroupModel().grant_user_permission(
            gr, TEST_USER_REGULAR_LOGIN, perm)

        # add repo permissions
        Session().commit()

        repo_name = 'ingroup_inherited_%s' % backend.alias
        repo_name_full = RepoGroup.url_sep().join([group_name, repo_name])
        description = 'description for newly created repo'
        self.app.post(
            route_path('repo_create'),
            fixture._get_repo_create_params(
                repo_private=False,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_description=description,
                repo_group=gr.group_id,
                repo_copy_permissions=True,
                csrf_token=csrf_token))

        # TODO: johbo: Cleanup to pytest fixture
        try:
            self.assert_repository_is_created_correctly(
                repo_name_full, description, backend)
        except Exception:
            RepoGroupModel().delete(group_name)
            Session().commit()
            raise

        # check if inherited permissions are applied
        new_repo = RepoModel().get_by_repo_name(repo_name_full)
        inherited_perms = UserRepoToPerm.query().filter(
            UserRepoToPerm.repository_id == new_repo.repo_id).all()
        assert len(inherited_perms) == 2

        assert TEST_USER_REGULAR_LOGIN in [
            x.user.username for x in inherited_perms]
        assert 'repository.write' in [
            x.permission.permission_name for x in inherited_perms]

        RepoModel().delete(repo_name_full)
        RepoGroupModel().delete(group_name)
        Session().commit()

    @pytest.mark.xfail_backends(
        "git", "hg", reason="Missing reposerver support")
    def test_create_with_clone_uri(self, autologin_user, backend, reposerver,
                                   csrf_token):
        source_repo = backend.create_repo(number_of_commits=2)
        source_repo_name = source_repo.repo_name
        reposerver.serve(source_repo.scm_instance())

        repo_name = backend.new_repo_name()
        response = self.app.post(
            route_path('repo_create'),
            fixture._get_repo_create_params(
                repo_private=False,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_description='',
                clone_uri=reposerver.url,
                csrf_token=csrf_token),
            status=302)

        # Should be redirected to the creating page
        response.mustcontain('repo_creating')

        # Expecting that both repositories have same history
        source_repo = RepoModel().get_by_repo_name(source_repo_name)
        source_vcs = source_repo.scm_instance()
        repo = RepoModel().get_by_repo_name(repo_name)
        repo_vcs = repo.scm_instance()
        assert source_vcs[0].message == repo_vcs[0].message
        assert source_vcs.count() == repo_vcs.count()
        assert source_vcs.commit_ids == repo_vcs.commit_ids

    @pytest.mark.xfail_backends("svn", reason="Depends on import support")
    def test_create_remote_repo_wrong_clone_uri(self, autologin_user, backend,
                                                csrf_token):
        repo_name = backend.new_repo_name()
        description = 'description for newly created repo'
        response = self.app.post(
            route_path('repo_create'),
            fixture._get_repo_create_params(
                repo_private=False,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_description=description,
                clone_uri='http://repo.invalid/repo',
                csrf_token=csrf_token))
        response.mustcontain('invalid clone url')

    @pytest.mark.xfail_backends("svn", reason="Depends on import support")
    def test_create_remote_repo_wrong_clone_uri_hg_svn(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.new_repo_name()
        description = 'description for newly created repo'
        response = self.app.post(
            route_path('repo_create'),
            fixture._get_repo_create_params(
                repo_private=False,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_description=description,
                clone_uri='svn+http://svn.invalid/repo',
                csrf_token=csrf_token))
        response.mustcontain('invalid clone url')

    def test_create_with_git_suffix(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.new_repo_name() + ".git"
        description = 'description for newly created repo'
        response = self.app.post(
            route_path('repo_create'),
            fixture._get_repo_create_params(
                repo_private=False,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_description=description,
                csrf_token=csrf_token))
        response.mustcontain('Repository name cannot end with .git')

    def test_default_user_cannot_access_private_repo_in_a_group(
            self, autologin_user, user_util, backend):

        group = user_util.create_repo_group()

        repo = backend.create_repo(
            repo_private=True, repo_group=group, repo_copy_permissions=True)

        permissions = _get_permission_for_user(
            user='default', repo=repo.repo_name)
        assert len(permissions) == 1
        assert permissions[0].permission.permission_name == 'repository.none'
        assert permissions[0].repository.private is True

    def test_create_on_top_level_without_permissions(self, backend):
        session = login_user_session(
            self.app, TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        csrf_token = auth.get_csrf_token(session)

        # revoke
        user_model = UserModel()
        # disable fork and create on default user
        user_model.revoke_perm(User.DEFAULT_USER, 'hg.create.repository')
        user_model.grant_perm(User.DEFAULT_USER, 'hg.create.none')
        user_model.revoke_perm(User.DEFAULT_USER, 'hg.fork.repository')
        user_model.grant_perm(User.DEFAULT_USER, 'hg.fork.none')

        # disable on regular user
        user_model.revoke_perm(TEST_USER_REGULAR_LOGIN, 'hg.create.repository')
        user_model.grant_perm(TEST_USER_REGULAR_LOGIN, 'hg.create.none')
        user_model.revoke_perm(TEST_USER_REGULAR_LOGIN, 'hg.fork.repository')
        user_model.grant_perm(TEST_USER_REGULAR_LOGIN, 'hg.fork.none')
        Session().commit()

        repo_name = backend.new_repo_name()
        description = 'description for newly created repo'
        response = self.app.post(
            route_path('repo_create'),
            fixture._get_repo_create_params(
                repo_private=False,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_description=description,
                csrf_token=csrf_token))

        response.mustcontain(
            u"You do not have the permission to store repositories in "
            u"the root location.")

    @mock.patch.object(RepoModel, '_create_filesystem_repo', error_function)
    def test_create_repo_when_filesystem_op_fails(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.new_repo_name()
        description = 'description for newly created repo'

        response = self.app.post(
            route_path('repo_create'),
            fixture._get_repo_create_params(
                repo_private=False,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_description=description,
                csrf_token=csrf_token))

        assert_session_flash(
            response, 'Error creating repository %s' % repo_name)
        # repo must not be in db
        assert backend.repo is None
        # repo must not be in filesystem !
        assert not repo_on_filesystem(repo_name)

    def assert_repository_is_created_correctly(
            self, repo_name, description, backend):
        repo_name_utf8 = safe_str(repo_name)

        # run the check page that triggers the flash message
        response = self.app.get(
            route_path('repo_creating_check', repo_name=safe_str(repo_name)))
        assert response.json == {u'result': True}

        flash_msg = u'Created repository <a href="/{}">{}</a>'.format(
            urllib.quote(repo_name_utf8), repo_name)
        assert_session_flash(response, flash_msg)

        # test if the repo was created in the database
        new_repo = RepoModel().get_by_repo_name(repo_name)

        assert new_repo.repo_name == repo_name
        assert new_repo.description == description

        # test if the repository is visible in the list ?
        response = self.app.get(
            h.route_path('repo_summary', repo_name=safe_str(repo_name)))
        response.mustcontain(repo_name)
        response.mustcontain(backend.alias)

        assert repo_on_filesystem(repo_name)
