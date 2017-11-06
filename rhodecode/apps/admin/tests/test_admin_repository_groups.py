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

import os
import pytest

from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.lib import helpers as h
from rhodecode.model.db import Repository, UserRepoToPerm, User
from rhodecode.model.meta import Session
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.tests import (
    assert_session_flash, TEST_USER_REGULAR_LOGIN, TESTS_TMP_PATH, TestController)
from rhodecode.tests.fixture import Fixture

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'repo_groups': ADMIN_PREFIX + '/repo_groups',
        'repo_group_new': ADMIN_PREFIX + '/repo_group/new',
        'repo_group_create': ADMIN_PREFIX + '/repo_group/create',

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
class TestAdminRepositoryGroups(object):
    def test_show_repo_groups(self, autologin_user):
        response = self.app.get(route_path('repo_groups'))
        response.mustcontain('data: []')

    def test_show_repo_groups_after_creating_group(self, autologin_user):
        fixture.create_repo_group('test_repo_group')
        response = self.app.get(route_path('repo_groups'))
        response.mustcontain('"name_raw": "test_repo_group"')
        fixture.destroy_repo_group('test_repo_group')

    def test_new(self, autologin_user):
        self.app.get(route_path('repo_group_new'))

    def test_new_with_parent_group(self, autologin_user, user_util):
        gr = user_util.create_repo_group()

        self.app.get(route_path('repo_group_new'),
                     params=dict(parent_group=gr.group_name))

    def test_new_by_regular_user_no_permission(self, autologin_regular_user):
        self.app.get(route_path('repo_group_new'), status=403)

    @pytest.mark.parametrize('repo_group_name', [
        'git_repo',
        'git_repo_ąć',
        'hg_repo',
        '12345',
        'hg_repo_ąć',
    ])
    def test_create(self, autologin_user, repo_group_name, csrf_token):
        repo_group_name_unicode = repo_group_name.decode('utf8')
        description = 'description for newly created repo group'

        response = self.app.post(
            route_path('repo_group_create'),
            fixture._get_group_create_params(
                group_name=repo_group_name,
                group_description=description,
                csrf_token=csrf_token))

        # run the check page that triggers the flash message
        repo_gr_url = h.route_path(
            'repo_group_home', repo_group_name=repo_group_name)

        assert_session_flash(
            response,
            'Created repository group <a href="%s">%s</a>' % (
                repo_gr_url, repo_group_name_unicode))

        # # test if the repo group was created in the database
        new_repo_group = RepoGroupModel()._get_repo_group(
            repo_group_name_unicode)
        assert new_repo_group is not None

        assert new_repo_group.group_name == repo_group_name_unicode
        assert new_repo_group.group_description == description

        # test if the repository is visible in the list ?
        response = self.app.get(repo_gr_url)
        response.mustcontain(repo_group_name)

        # test if the repository group was created on filesystem
        is_on_filesystem = os.path.isdir(
            os.path.join(TESTS_TMP_PATH, repo_group_name))
        if not is_on_filesystem:
            self.fail('no repo group %s in filesystem' % repo_group_name)

        RepoGroupModel().delete(repo_group_name_unicode)
        Session().commit()

    @pytest.mark.parametrize('repo_group_name', [
        'git_repo',
        'git_repo_ąć',
        'hg_repo',
        '12345',
        'hg_repo_ąć',
    ])
    def test_create_subgroup(self, autologin_user, user_util, repo_group_name, csrf_token):
        parent_group = user_util.create_repo_group()
        parent_group_name = parent_group.group_name

        expected_group_name = '{}/{}'.format(
            parent_group_name, repo_group_name)
        expected_group_name_unicode = expected_group_name.decode('utf8')

        try:
            response = self.app.post(
                route_path('repo_group_create'),
                fixture._get_group_create_params(
                    group_name=repo_group_name,
                    group_parent_id=parent_group.group_id,
                    group_description='Test desciption',
                    csrf_token=csrf_token))

            assert_session_flash(
                response,
                u'Created repository group <a href="%s">%s</a>' % (
                    h.route_path('repo_group_home',
                                 repo_group_name=expected_group_name),
                    expected_group_name_unicode))
        finally:
            RepoGroupModel().delete(expected_group_name_unicode)
            Session().commit()

    def test_user_with_creation_permissions_cannot_create_subgroups(
            self, autologin_regular_user, user_util):

        user_util.grant_user_permission(
            TEST_USER_REGULAR_LOGIN, 'hg.repogroup.create.true')
        parent_group = user_util.create_repo_group()
        parent_group_id = parent_group.group_id
        self.app.get(
            route_path('repo_group_new',
                       params=dict(parent_group=parent_group_id), ),
            status=403)
