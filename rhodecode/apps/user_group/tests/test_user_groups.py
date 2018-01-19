# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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

from rhodecode.tests import (
    TestController, assert_session_flash, TEST_USER_ADMIN_LOGIN)
from rhodecode.model.db import UserGroup
from rhodecode.model.meta import Session
from rhodecode.tests.fixture import Fixture

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib
    from rhodecode.apps._base import ADMIN_PREFIX

    base_url = {
        'user_groups': ADMIN_PREFIX + '/user_groups',
        'user_groups_data': ADMIN_PREFIX + '/user_groups_data',
        'user_group_members_data': ADMIN_PREFIX + '/user_groups/{user_group_id}/members',
        'user_groups_new': ADMIN_PREFIX + '/user_groups/new',
        'user_groups_create': ADMIN_PREFIX + '/user_groups/create',
        'edit_user_group': ADMIN_PREFIX + '/user_groups/{user_group_id}/edit',
        'edit_user_group_advanced_sync': ADMIN_PREFIX + '/user_groups/{user_group_id}/edit/advanced/sync',
        'edit_user_group_global_perms_update': ADMIN_PREFIX + '/user_groups/{user_group_id}/edit/global_permissions/update',
        'user_groups_update': ADMIN_PREFIX + '/user_groups/{user_group_id}/update',
        'user_groups_delete': ADMIN_PREFIX + '/user_groups/{user_group_id}/delete',

    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestUserGroupsView(TestController):

    def test_set_synchronization(self, user_util):
        self.log_user()
        user_group_name = user_util.create_user_group().users_group_name

        group = Session().query(UserGroup).filter(
            UserGroup.users_group_name == user_group_name).one()

        assert group.group_data.get('extern_type') is None

        # enable
        self.app.post(
            route_path('edit_user_group_advanced_sync',
                       user_group_id=group.users_group_id),
            params={'csrf_token': self.csrf_token}, status=302)

        group = Session().query(UserGroup).filter(
            UserGroup.users_group_name == user_group_name).one()
        assert group.group_data.get('extern_type') == 'manual'
        assert group.group_data.get('extern_type_set_by') == TEST_USER_ADMIN_LOGIN

        # disable
        self.app.post(
            route_path('edit_user_group_advanced_sync',
                user_group_id=group.users_group_id),
            params={'csrf_token': self.csrf_token}, status=302)

        group = Session().query(UserGroup).filter(
            UserGroup.users_group_name == user_group_name).one()
        assert group.group_data.get('extern_type') is None
        assert group.group_data.get('extern_type_set_by') == TEST_USER_ADMIN_LOGIN

    def test_delete_user_group(self, user_util):
        self.log_user()
        user_group_id = user_util.create_user_group().users_group_id

        group = Session().query(UserGroup).filter(
            UserGroup.users_group_id == user_group_id).one()

        self.app.post(
            route_path('user_groups_delete', user_group_id=group.users_group_id),
            params={'csrf_token': self.csrf_token})

        group = Session().query(UserGroup).filter(
            UserGroup.users_group_id == user_group_id).scalar()

        assert group is None

    @pytest.mark.parametrize('repo_create, repo_create_write, user_group_create, repo_group_create, fork_create, inherit_default_permissions, expect_error, expect_form_error', [
        ('hg.create.none', 'hg.create.write_on_repogroup.false', 'hg.usergroup.create.false', 'hg.repogroup.create.false', 'hg.fork.none', 'hg.inherit_default_perms.false', False, False),
        ('hg.create.repository', 'hg.create.write_on_repogroup.true', 'hg.usergroup.create.true', 'hg.repogroup.create.true', 'hg.fork.repository', 'hg.inherit_default_perms.false', False, False),
        ('hg.create.XXX', 'hg.create.write_on_repogroup.true', 'hg.usergroup.create.true', 'hg.repogroup.create.true', 'hg.fork.repository', 'hg.inherit_default_perms.false', False, True),
        ('', '', '', '', '', '', True, False),
    ])
    def test_global_permissions_on_user_group(
            self, repo_create, repo_create_write, user_group_create,
            repo_group_create, fork_create, expect_error, expect_form_error,
            inherit_default_permissions, user_util):

        self.log_user()
        user_group = user_util.create_user_group()

        user_group_name = user_group.users_group_name
        user_group_id = user_group.users_group_id

        # ENABLE REPO CREATE ON A GROUP
        perm_params = {
            'inherit_default_permissions': False,
            'default_repo_create': repo_create,
            'default_repo_create_on_write': repo_create_write,
            'default_user_group_create': user_group_create,
            'default_repo_group_create': repo_group_create,
            'default_fork_create': fork_create,
            'default_inherit_default_permissions': inherit_default_permissions,

            'csrf_token': self.csrf_token,
        }
        response = self.app.post(
            route_path('edit_user_group_global_perms_update',
                       user_group_id=user_group_id),
            params=perm_params)

        if expect_form_error:
            assert response.status_int == 200
            response.mustcontain('Value must be one of')
        else:
            if expect_error:
                msg = 'An error occurred during permissions saving'
            else:
                msg = 'User Group global permissions updated successfully'
                ug = UserGroup.get_by_group_name(user_group_name)
                del perm_params['csrf_token']
                del perm_params['inherit_default_permissions']
                assert perm_params == ug.get_default_perms()
            assert_session_flash(response, msg)

    def test_edit_view(self, user_util):
        self.log_user()

        user_group = user_util.create_user_group()
        self.app.get(
            route_path('edit_user_group',
                       user_group_id=user_group.users_group_id),
            status=200)

    def test_update_user_group(self, user_util):
        user = self.log_user()

        user_group = user_util.create_user_group()
        users_group_id = user_group.users_group_id
        new_name = user_group.users_group_name + '_CHANGE'

        params = [
            ('users_group_active', False),
            ('user_group_description', 'DESC'),
            ('users_group_name', new_name),
            ('user', user['username']),
            ('csrf_token', self.csrf_token),
            ('__start__', 'user_group_members:sequence'),
            ('__start__', 'member:mapping'),
            ('member_user_id', user['user_id']),
            ('type', 'existing'),
            ('__end__', 'member:mapping'),
            ('__end__', 'user_group_members:sequence'),
        ]

        self.app.post(
            route_path('user_groups_update',
                       user_group_id=users_group_id),
            params=params,
            status=302)

        user_group = UserGroup.get(users_group_id)
        assert user_group

        assert user_group.users_group_name == new_name
        assert user_group.user_group_description == 'DESC'
        assert user_group.users_group_active == False

    def test_update_user_group_name_conflicts(self, user_util):
        self.log_user()
        user_group_old = user_util.create_user_group()
        new_name = user_group_old.users_group_name

        user_group = user_util.create_user_group()

        params = dict(
            users_group_active=False,
            user_group_description='DESC',
            users_group_name=new_name,
            csrf_token=self.csrf_token)

        response = self.app.post(
            route_path('user_groups_update',
                       user_group_id=user_group.users_group_id),
            params=params,
            status=200)

        response.mustcontain('User group `{}` already exists'.format(
            new_name))

    def test_update_members_from_user_ids(self, user_regular):
        uid = user_regular.user_id
        username = user_regular.username
        self.log_user()

        user_group = fixture.create_user_group('test_gr_ids')
        assert user_group.members == []
        assert user_group.user != user_regular
        expected_active_state = not user_group.users_group_active

        form_data = [
            ('csrf_token', self.csrf_token),
            ('user', username),
            ('users_group_name', 'changed_name'),
            ('users_group_active', expected_active_state),
            ('user_group_description', 'changed_description'),

            ('__start__', 'user_group_members:sequence'),
            ('__start__', 'member:mapping'),
            ('member_user_id', uid),
            ('type', 'existing'),
            ('__end__', 'member:mapping'),
            ('__end__', 'user_group_members:sequence'),
        ]
        ugid = user_group.users_group_id
        self.app.post(
            route_path('user_groups_update', user_group_id=ugid), form_data)

        user_group = UserGroup.get(ugid)
        assert user_group

        assert user_group.members[0].user_id == uid
        assert user_group.user_id == uid
        assert 'changed_name' in user_group.users_group_name
        assert 'changed_description' in user_group.user_group_description
        assert user_group.users_group_active == expected_active_state

        fixture.destroy_user_group(user_group)
