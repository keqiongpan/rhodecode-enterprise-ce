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

import mock
import pytest

from rhodecode.lib.utils2 import str2bool
from rhodecode.lib.vcs.exceptions import RepositoryRequirementError
from rhodecode.model.db import Repository, UserRepoToPerm, Permission, User
from rhodecode.model.meta import Session
from rhodecode.tests import (
    TEST_USER_ADMIN_LOGIN, TEST_USER_REGULAR_LOGIN, assert_session_flash)
from rhodecode.tests.fixture import Fixture

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'edit_repo': '/{repo_name}/settings',
        'edit_repo_advanced': '/{repo_name}/settings/advanced',
        'edit_repo_caches': '/{repo_name}/settings/caches',
        'edit_repo_perms': '/{repo_name}/settings/permissions',
        'edit_repo_vcs': '/{repo_name}/settings/vcs',
        'edit_repo_issuetracker': '/{repo_name}/settings/issue_trackers',
        'edit_repo_fields': '/{repo_name}/settings/fields',
        'edit_repo_remote': '/{repo_name}/settings/remote',
        'edit_repo_statistics': '/{repo_name}/settings/statistics',
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


@pytest.mark.usefixtures('autologin_user', 'app')
class TestAdminRepoSettings(object):
    @pytest.mark.parametrize('urlname', [
        'edit_repo',
        'edit_repo_caches',
        'edit_repo_perms',
        'edit_repo_advanced',
        'edit_repo_vcs',
        'edit_repo_issuetracker',
        'edit_repo_fields',
        'edit_repo_remote',
        'edit_repo_statistics',
    ])
    def test_show_page(self, urlname, app, backend):
        app.get(route_path(urlname, repo_name=backend.repo_name), status=200)

    def test_edit_accessible_when_missing_requirements(
            self, backend_hg, autologin_user):
        scm_patcher = mock.patch.object(
            Repository, 'scm_instance', side_effect=RepositoryRequirementError)
        with scm_patcher:
            self.app.get(route_path('edit_repo', repo_name=backend_hg.repo_name))

    @pytest.mark.parametrize('update_settings', [
        {'repo_description': 'alter-desc'},
        {'repo_owner': TEST_USER_REGULAR_LOGIN},
        {'repo_private': 'true'},
        {'repo_enable_locking': 'true'},
        {'repo_enable_downloads': 'true'},
    ])
    def test_update_repo_settings(self, update_settings, csrf_token, backend, user_util):
        repo = user_util.create_repo(repo_type=backend.alias)
        repo_name = repo.repo_name

        params = fixture._get_repo_create_params(
                csrf_token=csrf_token,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_owner=TEST_USER_ADMIN_LOGIN,
                repo_description='DESC',

                repo_private='false',
                repo_enable_locking='false',
                repo_enable_downloads='false')
        params.update(update_settings)
        self.app.post(
            route_path('edit_repo', repo_name=repo_name),
            params=params, status=302)

        repo = Repository.get_by_repo_name(repo_name)
        assert repo.user.username == \
               update_settings.get('repo_owner', repo.user.username)

        assert repo.description == \
               update_settings.get('repo_description', repo.description)

        assert repo.private == \
               str2bool(update_settings.get(
                   'repo_private', repo.private))

        assert repo.enable_locking == \
               str2bool(update_settings.get(
                   'repo_enable_locking', repo.enable_locking))

        assert repo.enable_downloads == \
               str2bool(update_settings.get(
                   'repo_enable_downloads', repo.enable_downloads))

    def test_update_repo_name_via_settings(self, csrf_token, user_util, backend):
        repo = user_util.create_repo(repo_type=backend.alias)
        repo_name = repo.repo_name

        repo_group = user_util.create_repo_group()
        repo_group_name = repo_group.group_name
        new_name = repo_group_name + '_' + repo_name

        params = fixture._get_repo_create_params(
                csrf_token=csrf_token,
                repo_name=new_name,
                repo_type=backend.alias,
                repo_owner=TEST_USER_ADMIN_LOGIN,
                repo_description='DESC',
                repo_private='false',
                repo_enable_locking='false',
                repo_enable_downloads='false')
        self.app.post(
            route_path('edit_repo', repo_name=repo_name),
            params=params, status=302)
        repo = Repository.get_by_repo_name(new_name)
        assert repo.repo_name == new_name

    def test_update_repo_group_via_settings(self, csrf_token, user_util, backend):
        repo = user_util.create_repo(repo_type=backend.alias)
        repo_name = repo.repo_name

        repo_group = user_util.create_repo_group()
        repo_group_name = repo_group.group_name
        repo_group_id = repo_group.group_id

        new_name = repo_group_name + '/' + repo_name
        params = fixture._get_repo_create_params(
                csrf_token=csrf_token,
                repo_name=repo_name,
                repo_type=backend.alias,
                repo_owner=TEST_USER_ADMIN_LOGIN,
                repo_description='DESC',
                repo_group=repo_group_id,
                repo_private='false',
                repo_enable_locking='false',
                repo_enable_downloads='false')
        self.app.post(
            route_path('edit_repo', repo_name=repo_name),
            params=params, status=302)
        repo = Repository.get_by_repo_name(new_name)
        assert repo.repo_name == new_name

    def test_set_private_flag_sets_default_user_permissions_to_none(
            self, autologin_user, backend, csrf_token):

        # initially repository perm should be read
        perm = _get_permission_for_user(user='default', repo=backend.repo_name)
        assert len(perm) == 1
        assert perm[0].permission.permission_name == 'repository.read'
        assert not backend.repo.private

        response = self.app.post(
            route_path('edit_repo', repo_name=backend.repo_name),
            params=fixture._get_repo_create_params(
                repo_private='true',
                repo_name=backend.repo_name,
                repo_type=backend.alias,
                repo_owner=TEST_USER_ADMIN_LOGIN,
                csrf_token=csrf_token), status=302)

        assert_session_flash(
            response,
            msg='Repository %s updated successfully' % (backend.repo_name))

        repo = Repository.get_by_repo_name(backend.repo_name)
        assert repo.private is True

        # now the repo default permission should be None
        perm = _get_permission_for_user(user='default', repo=backend.repo_name)
        assert len(perm) == 1
        assert perm[0].permission.permission_name == 'repository.none'

        response = self.app.post(
            route_path('edit_repo', repo_name=backend.repo_name),
            params=fixture._get_repo_create_params(
                repo_private='false',
                repo_name=backend.repo_name,
                repo_type=backend.alias,
                repo_owner=TEST_USER_ADMIN_LOGIN,
                csrf_token=csrf_token), status=302)

        assert_session_flash(
            response,
            msg='Repository %s updated successfully' % (backend.repo_name))
        assert backend.repo.private is False

        # we turn off private now the repo default permission should stay None
        perm = _get_permission_for_user(user='default', repo=backend.repo_name)
        assert len(perm) == 1
        assert perm[0].permission.permission_name == 'repository.none'

        # update this permission back
        perm[0].permission = Permission.get_by_key('repository.read')
        Session().add(perm[0])
        Session().commit()
