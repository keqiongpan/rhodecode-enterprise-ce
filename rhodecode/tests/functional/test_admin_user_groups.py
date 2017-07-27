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

from rhodecode.tests import (
    TestController, url, assert_session_flash, link_to, TEST_USER_ADMIN_LOGIN)
from rhodecode.model.db import User, UserGroup
from rhodecode.model.meta import Session
from rhodecode.tests.fixture import Fixture

TEST_USER_GROUP = 'admins_test'

fixture = Fixture()


class TestAdminUsersGroupsController(TestController):

    def test_create(self):
        self.log_user()
        users_group_name = TEST_USER_GROUP
        response = self.app.post(url('users_groups'), {
            'users_group_name': users_group_name,
            'user_group_description': 'DESC',
            'active': True,
            'csrf_token': self.csrf_token})

        user_group_link = link_to(
            users_group_name,
            url('edit_users_group',
                user_group_id=UserGroup.get_by_group_name(
                    users_group_name).users_group_id))
        assert_session_flash(
            response,
            'Created user group %s' % user_group_link)

    def test_set_synchronization(self):
        self.log_user()
        users_group_name = TEST_USER_GROUP + 'sync'
        response = self.app.post(url('users_groups'), {
            'users_group_name': users_group_name,
            'user_group_description': 'DESC',
            'active': True,
            'csrf_token': self.csrf_token})

        group = Session().query(UserGroup).filter(
            UserGroup.users_group_name == users_group_name).one()

        assert group.group_data.get('extern_type') is None

        # enable
        self.app.post(
            url('edit_user_group_advanced_sync', user_group_id=group.users_group_id),
            params={'csrf_token': self.csrf_token}, status=302)

        group = Session().query(UserGroup).filter(
            UserGroup.users_group_name == users_group_name).one()
        assert group.group_data.get('extern_type') == 'manual'
        assert group.group_data.get('extern_type_set_by') == TEST_USER_ADMIN_LOGIN

        # disable
        self.app.post(
            url('edit_user_group_advanced_sync',
                user_group_id=group.users_group_id),
            params={'csrf_token': self.csrf_token}, status=302)

        group = Session().query(UserGroup).filter(
            UserGroup.users_group_name == users_group_name).one()
        assert group.group_data.get('extern_type') is None
        assert group.group_data.get('extern_type_set_by') == TEST_USER_ADMIN_LOGIN

    def test_delete(self):
        self.log_user()
        users_group_name = TEST_USER_GROUP + 'another'
        response = self.app.post(url('users_groups'), {
            'users_group_name': users_group_name,
            'user_group_description': 'DESC',
            'active': True,
            'csrf_token': self.csrf_token})

        user_group_link = link_to(
            users_group_name,
            url('edit_users_group',
                user_group_id=UserGroup.get_by_group_name(
                    users_group_name).users_group_id))
        assert_session_flash(
            response,
            'Created user group %s' % user_group_link)

        group = Session().query(UserGroup).filter(
            UserGroup.users_group_name == users_group_name).one()

        self.app.post(
            url('delete_users_group', user_group_id=group.users_group_id),
            params={'_method': 'delete', 'csrf_token': self.csrf_token})

        group = Session().query(UserGroup).filter(
            UserGroup.users_group_name == users_group_name).scalar()

        assert group is None

    @pytest.mark.parametrize('repo_create, repo_create_write, user_group_create, repo_group_create, fork_create, inherit_default_permissions, expect_error, expect_form_error', [
        ('hg.create.none', 'hg.create.write_on_repogroup.false', 'hg.usergroup.create.false', 'hg.repogroup.create.false', 'hg.fork.none', 'hg.inherit_default_perms.false', False, False),
        ('hg.create.repository', 'hg.create.write_on_repogroup.true', 'hg.usergroup.create.true', 'hg.repogroup.create.true', 'hg.fork.repository', 'hg.inherit_default_perms.false', False, False),
        ('hg.create.XXX', 'hg.create.write_on_repogroup.true', 'hg.usergroup.create.true', 'hg.repogroup.create.true', 'hg.fork.repository', 'hg.inherit_default_perms.false', False, True),
        ('', '', '', '', '', '', True, False),
    ])
    def test_global_perms_on_group(
            self, repo_create, repo_create_write, user_group_create,
            repo_group_create, fork_create, expect_error, expect_form_error,
            inherit_default_permissions):
        self.log_user()
        users_group_name = TEST_USER_GROUP + 'another2'
        response = self.app.post(url('users_groups'),
                                 {'users_group_name': users_group_name,
                                  'user_group_description': 'DESC',
                                  'active': True,
                                  'csrf_token': self.csrf_token})

        ug = UserGroup.get_by_group_name(users_group_name)
        user_group_link = link_to(
            users_group_name,
            url('edit_users_group', user_group_id=ug.users_group_id))
        assert_session_flash(
            response,
            'Created user group %s' % user_group_link)
        response.follow()

        # ENABLE REPO CREATE ON A GROUP
        perm_params = {
            'inherit_default_permissions': False,
            'default_repo_create': repo_create,
            'default_repo_create_on_write': repo_create_write,
            'default_user_group_create': user_group_create,
            'default_repo_group_create': repo_group_create,
            'default_fork_create': fork_create,
            'default_inherit_default_permissions': inherit_default_permissions,

            '_method': 'put',
            'csrf_token': self.csrf_token,
        }
        response = self.app.post(
            url('edit_user_group_global_perms',
                user_group_id=ug.users_group_id),
            params=perm_params)

        if expect_form_error:
            assert response.status_int == 200
            response.mustcontain('Value must be one of')
        else:
            if expect_error:
                msg = 'An error occurred during permissions saving'
            else:
                msg = 'User Group global permissions updated successfully'
                ug = UserGroup.get_by_group_name(users_group_name)
                del perm_params['_method']
                del perm_params['csrf_token']
                del perm_params['inherit_default_permissions']
                assert perm_params == ug.get_default_perms()
            assert_session_flash(response, msg)

        fixture.destroy_user_group(users_group_name)

    def test_edit_autocomplete(self):
        self.log_user()
        ug = fixture.create_user_group(TEST_USER_GROUP, skip_if_exists=True)
        response = self.app.get(
            url('edit_users_group', user_group_id=ug.users_group_id))
        fixture.destroy_user_group(TEST_USER_GROUP)

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
            ('_method', 'put'),
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
        self.app.post(url('update_users_group', user_group_id=ugid), form_data)

        user_group = UserGroup.get(ugid)
        assert user_group

        assert user_group.members[0].user_id == uid
        assert user_group.user_id == uid
        assert 'changed_name' in user_group.users_group_name
        assert 'changed_description' in user_group.user_group_description
        assert user_group.users_group_active == expected_active_state

        fixture.destroy_user_group(user_group)
