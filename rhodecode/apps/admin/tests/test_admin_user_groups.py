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

from rhodecode.model.db import UserGroup, User
from rhodecode.model.meta import Session

from rhodecode.tests import (
    TestController, TEST_USER_REGULAR_LOGIN, assert_session_flash)
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
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestAdminUserGroupsView(TestController):

    def test_show_users(self):
        self.log_user()
        self.app.get(route_path('user_groups'))

    def test_show_user_groups_data(self, xhr_header):
        self.log_user()
        response = self.app.get(route_path(
            'user_groups_data'), extra_environ=xhr_header)

        all_user_groups = UserGroup.query().count()
        assert response.json['recordsTotal'] == all_user_groups

    def test_show_user_groups_data_filtered(self, xhr_header):
        self.log_user()
        response = self.app.get(route_path(
            'user_groups_data', params={'search[value]': 'empty_search'}),
            extra_environ=xhr_header)

        all_user_groups = UserGroup.query().count()
        assert response.json['recordsTotal'] == all_user_groups
        assert response.json['recordsFiltered'] == 0

    def test_usergroup_escape(self, user_util, xhr_header):
        self.log_user()

        xss_img = '<img src="/image1" onload="alert(\'Hello, World!\');">'
        user = user_util.create_user()
        user.name = xss_img
        user.lastname = xss_img
        Session().add(user)
        Session().commit()

        user_group = user_util.create_user_group()

        user_group.users_group_name = xss_img
        user_group.user_group_description = '<strong onload="alert();">DESC</strong>'

        response = self.app.get(
            route_path('user_groups_data'), extra_environ=xhr_header)

        response.mustcontain(
            '&lt;strong onload=&#34;alert();&#34;&gt;DESC&lt;/strong&gt;')
        response.mustcontain(
            '&lt;img src=&#34;/image1&#34; onload=&#34;'
            'alert(&#39;Hello, World!&#39;);&#34;&gt;')

    def test_edit_user_group_autocomplete_empty_members(self, xhr_header, user_util):
        self.log_user()
        ug = user_util.create_user_group()
        response = self.app.get(
            route_path('user_group_members_data', user_group_id=ug.users_group_id),
            extra_environ=xhr_header)

        assert response.json == {'members': []}

    def test_edit_user_group_autocomplete_members(self, xhr_header, user_util):
        self.log_user()
        members = [u.user_id for u in User.get_all()]
        ug = user_util.create_user_group(members=members)
        response = self.app.get(
            route_path('user_group_members_data',
                       user_group_id=ug.users_group_id),
            extra_environ=xhr_header)

        assert len(response.json['members']) == len(members)

    def test_creation_page(self):
        self.log_user()
        self.app.get(route_path('user_groups_new'), status=200)

    def test_create(self):
        from rhodecode.lib import helpers as h

        self.log_user()
        users_group_name = 'test_user_group'
        response = self.app.post(route_path('user_groups_create'), {
            'users_group_name': users_group_name,
            'user_group_description': 'DESC',
            'active': True,
            'csrf_token': self.csrf_token})

        user_group_id = UserGroup.get_by_group_name(
            users_group_name).users_group_id

        user_group_link = h.link_to(
            users_group_name,
            route_path('edit_user_group', user_group_id=user_group_id))

        assert_session_flash(
            response,
            'Created user group %s' % user_group_link)

        fixture.destroy_user_group(users_group_name)

    def test_create_with_empty_name(self):
        self.log_user()

        response = self.app.post(route_path('user_groups_create'), {
            'users_group_name': '',
            'user_group_description': 'DESC',
            'active': True,
            'csrf_token': self.csrf_token}, status=200)

        response.mustcontain('Please enter a value')

    def test_create_duplicate(self, user_util):
        self.log_user()

        user_group = user_util.create_user_group()
        duplicate_name = user_group.users_group_name
        response = self.app.post(route_path('user_groups_create'), {
            'users_group_name': duplicate_name,
            'user_group_description': 'DESC',
            'active': True,
            'csrf_token': self.csrf_token}, status=200)

        response.mustcontain(
            'User group `{}` already exists'.format(duplicate_name))
