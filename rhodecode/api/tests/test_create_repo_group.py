# -*- coding: utf-8 -*-

# Copyright (C) 2010-2016  RhodeCode GmbH
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

from rhodecode.model.meta import Session
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.user import UserModel
from rhodecode.tests import TEST_USER_ADMIN_LOGIN
from rhodecode.api.tests.utils import (
    build_data, api_call, assert_ok, assert_error, crash)
from rhodecode.tests.fixture import Fixture


fixture = Fixture()


@pytest.mark.usefixtures("testuser_api", "app")
class TestCreateRepoGroup(object):
    def test_api_create_repo_group(self):
        repo_group_name = 'api-repo-group'

        repo_group = RepoGroupModel.cls.get_by_group_name(repo_group_name)
        assert repo_group is None

        id_, params = build_data(
            self.apikey, 'create_repo_group',
            group_name=repo_group_name,
            owner=TEST_USER_ADMIN_LOGIN,)
        response = api_call(self.app, params)

        repo_group = RepoGroupModel.cls.get_by_group_name(repo_group_name)
        assert repo_group is not None
        ret = {
            'msg': 'Created new repo group `%s`' % (repo_group_name,),
            'repo_group': repo_group.get_api_data()
        }
        expected = ret
        try:
            assert_ok(id_, expected, given=response.body)
        finally:
            fixture.destroy_repo_group(repo_group_name)

    def test_api_create_repo_group_in_another_group(self):
        repo_group_name = 'api-repo-group'

        repo_group = RepoGroupModel.cls.get_by_group_name(repo_group_name)
        assert repo_group is None
        # create the parent
        fixture.create_repo_group(repo_group_name)

        full_repo_group_name = repo_group_name+'/'+repo_group_name
        id_, params = build_data(
            self.apikey, 'create_repo_group',
            group_name=full_repo_group_name,
            owner=TEST_USER_ADMIN_LOGIN,
            copy_permissions=True)
        response = api_call(self.app, params)

        repo_group = RepoGroupModel.cls.get_by_group_name(full_repo_group_name)
        assert repo_group is not None
        ret = {
            'msg': 'Created new repo group `%s`' % (full_repo_group_name,),
            'repo_group': repo_group.get_api_data()
        }
        expected = ret
        try:
            assert_ok(id_, expected, given=response.body)
        finally:
            fixture.destroy_repo_group(full_repo_group_name)
            fixture.destroy_repo_group(repo_group_name)

    def test_api_create_repo_group_in_another_group_not_existing(self):
        repo_group_name = 'api-repo-group-no'

        repo_group = RepoGroupModel.cls.get_by_group_name(repo_group_name)
        assert repo_group is None

        full_repo_group_name = repo_group_name+'/'+repo_group_name
        id_, params = build_data(
            self.apikey, 'create_repo_group',
            group_name=full_repo_group_name,
            owner=TEST_USER_ADMIN_LOGIN,
            copy_permissions=True)
        response = api_call(self.app, params)
        expected = {
            'repo_group':
                'Parent repository group `{}` does not exist'.format(
                    repo_group_name)}
        assert_error(id_, expected, given=response.body)

    def test_api_create_repo_group_that_exists(self):
        repo_group_name = 'api-repo-group'

        repo_group = RepoGroupModel.cls.get_by_group_name(repo_group_name)
        assert repo_group is None

        fixture.create_repo_group(repo_group_name)
        id_, params = build_data(
            self.apikey, 'create_repo_group',
            group_name=repo_group_name,
            owner=TEST_USER_ADMIN_LOGIN,)
        response = api_call(self.app, params)
        expected = {
            'unique_repo_group_name':
                'Repository group with name `{}` already exists'.format(
                    repo_group_name)}
        try:
            assert_error(id_, expected, given=response.body)
        finally:
            fixture.destroy_repo_group(repo_group_name)

    def test_api_create_repo_group_regular_user_wit_root_location_perms(
            self, user_util):
        regular_user = user_util.create_user()
        regular_user_api_key = regular_user.api_key

        repo_group_name = 'api-repo-group-by-regular-user'

        usr = UserModel().get_by_username(regular_user.username)
        usr.inherit_default_permissions = False
        Session().add(usr)

        UserModel().grant_perm(
            regular_user.username, 'hg.repogroup.create.true')
        Session().commit()

        repo_group = RepoGroupModel.cls.get_by_group_name(repo_group_name)
        assert repo_group is None

        id_, params = build_data(
            regular_user_api_key, 'create_repo_group',
            group_name=repo_group_name)
        response = api_call(self.app, params)

        repo_group = RepoGroupModel.cls.get_by_group_name(repo_group_name)
        assert repo_group is not None
        expected = {
            'msg': 'Created new repo group `%s`' % (repo_group_name,),
            'repo_group': repo_group.get_api_data()
        }
        try:
            assert_ok(id_, expected, given=response.body)
        finally:
            fixture.destroy_repo_group(repo_group_name)

    def test_api_create_repo_group_regular_user_with_admin_perms_to_parent(
            self, user_util):

        repo_group_name = 'api-repo-group-parent'

        repo_group = RepoGroupModel.cls.get_by_group_name(repo_group_name)
        assert repo_group is None
        # create the parent
        fixture.create_repo_group(repo_group_name)

        # user perms
        regular_user = user_util.create_user()
        regular_user_api_key = regular_user.api_key

        usr = UserModel().get_by_username(regular_user.username)
        usr.inherit_default_permissions = False
        Session().add(usr)

        RepoGroupModel().grant_user_permission(
            repo_group_name, regular_user.username, 'group.admin')
        Session().commit()

        full_repo_group_name = repo_group_name + '/' + repo_group_name
        id_, params = build_data(
            regular_user_api_key, 'create_repo_group',
            group_name=full_repo_group_name)
        response = api_call(self.app, params)

        repo_group = RepoGroupModel.cls.get_by_group_name(full_repo_group_name)
        assert repo_group is not None
        expected = {
            'msg': 'Created new repo group `{}`'.format(full_repo_group_name),
            'repo_group': repo_group.get_api_data()
        }
        try:
            assert_ok(id_, expected, given=response.body)
        finally:
            fixture.destroy_repo_group(full_repo_group_name)
            fixture.destroy_repo_group(repo_group_name)

    def test_api_create_repo_group_regular_user_no_permission_to_create_to_root_level(self):
        repo_group_name = 'api-repo-group'

        id_, params = build_data(
            self.apikey_regular, 'create_repo_group',
            group_name=repo_group_name)
        response = api_call(self.app, params)

        expected = {
            'repo_group':
                u'You do not have the permission to store '
                u'repository groups in the root location.'}
        assert_error(id_, expected, given=response.body)

    def test_api_create_repo_group_regular_user_no_parent_group_perms(self):
        repo_group_name = 'api-repo-group-regular-user'

        repo_group = RepoGroupModel.cls.get_by_group_name(repo_group_name)
        assert repo_group is None
        # create the parent
        fixture.create_repo_group(repo_group_name)

        full_repo_group_name = repo_group_name+'/'+repo_group_name

        id_, params = build_data(
            self.apikey_regular, 'create_repo_group',
            group_name=full_repo_group_name)
        response = api_call(self.app, params)

        expected = {
            'repo_group':
                'Parent repository group `{}` does not exist'.format(
                    repo_group_name)}
        try:
            assert_error(id_, expected, given=response.body)
        finally:
            fixture.destroy_repo_group(repo_group_name)

    def test_api_create_repo_group_regular_user_no_permission_to_specify_owner(
            self):
        repo_group_name = 'api-repo-group'

        id_, params = build_data(
            self.apikey_regular, 'create_repo_group',
            group_name=repo_group_name,
            owner=TEST_USER_ADMIN_LOGIN,)
        response = api_call(self.app, params)

        expected = "Only RhodeCode super-admin can specify `owner` param"
        assert_error(id_, expected, given=response.body)

    @mock.patch.object(RepoGroupModel, 'create', crash)
    def test_api_create_repo_group_exception_occurred(self):
        repo_group_name = 'api-repo-group'

        repo_group = RepoGroupModel.cls.get_by_group_name(repo_group_name)
        assert repo_group is None

        id_, params = build_data(
            self.apikey, 'create_repo_group',
            group_name=repo_group_name,
            owner=TEST_USER_ADMIN_LOGIN,)
        response = api_call(self.app, params)
        expected = 'failed to create repo group `%s`' % (repo_group_name,)
        assert_error(id_, expected, given=response.body)

    def test_create_group_with_extra_slashes_in_name(self, user_util):
        existing_repo_group = user_util.create_repo_group()
        dirty_group_name = '//{}//group2//'.format(
            existing_repo_group.group_name)
        cleaned_group_name = '{}/group2'.format(
            existing_repo_group.group_name)

        id_, params = build_data(
            self.apikey, 'create_repo_group',
            group_name=dirty_group_name,
            owner=TEST_USER_ADMIN_LOGIN,)
        response = api_call(self.app, params)
        repo_group = RepoGroupModel.cls.get_by_group_name(cleaned_group_name)
        expected = {
            'msg': 'Created new repo group `%s`' % (cleaned_group_name,),
            'repo_group': repo_group.get_api_data()
        }
        assert_ok(id_, expected, given=response.body)
        fixture.destroy_repo_group(cleaned_group_name)
