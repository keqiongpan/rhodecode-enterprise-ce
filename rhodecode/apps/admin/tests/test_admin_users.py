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

from rhodecode.model.db import User, UserApiKeys, UserEmailMap
from rhodecode.model.meta import Session
from rhodecode.model.user import UserModel

from rhodecode.tests import (
    TestController, TEST_USER_REGULAR_LOGIN, assert_session_flash)
from rhodecode.tests.fixture import Fixture

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib
    from rhodecode.apps._base import ADMIN_PREFIX

    base_url = {
        'users':
            ADMIN_PREFIX + '/users',
        'users_data':
            ADMIN_PREFIX + '/users_data',
        'edit_user_auth_tokens':
            ADMIN_PREFIX + '/users/{user_id}/edit/auth_tokens',
        'edit_user_auth_tokens_add':
            ADMIN_PREFIX + '/users/{user_id}/edit/auth_tokens/new',
        'edit_user_auth_tokens_delete':
            ADMIN_PREFIX + '/users/{user_id}/edit/auth_tokens/delete',

        'edit_user_emails':
            ADMIN_PREFIX + '/users/{user_id}/edit/emails',
        'edit_user_emails_add':
            ADMIN_PREFIX + '/users/{user_id}/edit/emails/new',
        'edit_user_emails_delete':
            ADMIN_PREFIX + '/users/{user_id}/edit/emails/delete',

        'edit_user_ips':
            ADMIN_PREFIX + '/users/{user_id}/edit/ips',
        'edit_user_ips_add':
            ADMIN_PREFIX + '/users/{user_id}/edit/ips/new',
        'edit_user_ips_delete':
            ADMIN_PREFIX + '/users/{user_id}/edit/ips/delete',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestAdminUsersView(TestController):

    def test_show_users(self):
        self.log_user()
        self.app.get(route_path('users'))

    def test_show_users_data(self, xhr_header):
        self.log_user()
        response = self.app.get(route_path(
            'users_data'), extra_environ=xhr_header)

        all_users = User.query().filter(
            User.username != User.DEFAULT_USER).count()
        assert response.json['recordsTotal'] == all_users

    def test_show_users_data_filtered(self, xhr_header):
        self.log_user()
        response = self.app.get(route_path(
            'users_data', params={'search[value]': 'empty_search'}),
            extra_environ=xhr_header)

        all_users = User.query().filter(
            User.username != User.DEFAULT_USER).count()
        assert response.json['recordsTotal'] == all_users
        assert response.json['recordsFiltered'] == 0

    def test_auth_tokens_default_user(self):
        self.log_user()
        user = User.get_default_user()
        response = self.app.get(
            route_path('edit_user_auth_tokens', user_id=user.user_id),
            status=302)

    def test_auth_tokens(self):
        self.log_user()

        user = User.get_by_username(TEST_USER_REGULAR_LOGIN)
        response = self.app.get(
            route_path('edit_user_auth_tokens', user_id=user.user_id))
        for token in user.auth_tokens:
            response.mustcontain(token)
            response.mustcontain('never')

    @pytest.mark.parametrize("desc, lifetime", [
        ('forever', -1),
        ('5mins', 60*5),
        ('30days', 60*60*24*30),
    ])
    def test_add_auth_token(self, desc, lifetime, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        response = self.app.post(
            route_path('edit_user_auth_tokens_add', user_id=user_id),
            {'description': desc, 'lifetime': lifetime,
             'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Auth token successfully created')

        response = response.follow()
        user = User.get(user_id)
        for auth_token in user.auth_tokens:
            response.mustcontain(auth_token)

    def test_delete_auth_token(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id
        keys = user.extra_auth_tokens
        assert 2 == len(keys)

        response = self.app.post(
            route_path('edit_user_auth_tokens_add', user_id=user_id),
            {'description': 'desc', 'lifetime': -1,
             'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Auth token successfully created')
        response.follow()

        # now delete our key
        keys = UserApiKeys.query().filter(UserApiKeys.user_id == user_id).all()
        assert 3 == len(keys)

        response = self.app.post(
            route_path('edit_user_auth_tokens_delete', user_id=user_id),
            {'del_auth_token': keys[0].user_api_key_id,
             'csrf_token': self.csrf_token})

        assert_session_flash(response, 'Auth token successfully deleted')
        keys = UserApiKeys.query().filter(UserApiKeys.user_id == user_id).all()
        assert 2 == len(keys)

    def test_ips(self):
        self.log_user()
        user = User.get_by_username(TEST_USER_REGULAR_LOGIN)
        response = self.app.get(route_path('edit_user_ips', user_id=user.user_id))
        response.mustcontain('All IP addresses are allowed')

    @pytest.mark.parametrize("test_name, ip, ip_range, failure", [
        ('127/24', '127.0.0.1/24', '127.0.0.0 - 127.0.0.255', False),
        ('10/32', '10.0.0.10/32', '10.0.0.10 - 10.0.0.10', False),
        ('0/16', '0.0.0.0/16', '0.0.0.0 - 0.0.255.255', False),
        ('0/8', '0.0.0.0/8', '0.0.0.0 - 0.255.255.255', False),
        ('127_bad_mask', '127.0.0.1/99', '127.0.0.1 - 127.0.0.1', True),
        ('127_bad_ip', 'foobar', 'foobar', True),
    ])
    def test_ips_add(self, user_util, test_name, ip, ip_range, failure):
        self.log_user()
        user = user_util.create_user(username=test_name)
        user_id = user.user_id

        response = self.app.post(
            route_path('edit_user_ips_add', user_id=user_id),
            params={'new_ip': ip, 'csrf_token': self.csrf_token})

        if failure:
            assert_session_flash(
                response, 'Please enter a valid IPv4 or IpV6 address')
            response = self.app.get(route_path('edit_user_ips', user_id=user_id))

            response.mustcontain(no=[ip])
            response.mustcontain(no=[ip_range])

        else:
            response = self.app.get(route_path('edit_user_ips', user_id=user_id))
            response.mustcontain(ip)
            response.mustcontain(ip_range)

    def test_ips_delete(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id
        ip = '127.0.0.1/32'
        ip_range = '127.0.0.1 - 127.0.0.1'
        new_ip = UserModel().add_extra_ip(user_id, ip)
        Session().commit()
        new_ip_id = new_ip.ip_id

        response = self.app.get(route_path('edit_user_ips', user_id=user_id))
        response.mustcontain(ip)
        response.mustcontain(ip_range)

        self.app.post(
            route_path('edit_user_ips_delete', user_id=user_id),
            params={'del_ip_id': new_ip_id, 'csrf_token': self.csrf_token})

        response = self.app.get(route_path('edit_user_ips', user_id=user_id))
        response.mustcontain('All IP addresses are allowed')
        response.mustcontain(no=[ip])
        response.mustcontain(no=[ip_range])

    def test_emails(self):
        self.log_user()
        user = User.get_by_username(TEST_USER_REGULAR_LOGIN)
        response = self.app.get(route_path('edit_user_emails', user_id=user.user_id))
        response.mustcontain('No additional emails specified')

    def test_emails_add(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        self.app.post(
            route_path('edit_user_emails_add', user_id=user_id),
            params={'new_email': 'example@rhodecode.com',
                    'csrf_token': self.csrf_token})

        response = self.app.get(route_path('edit_user_emails', user_id=user_id))
        response.mustcontain('example@rhodecode.com')

    def test_emails_add_existing_email(self, user_util, user_regular):
        existing_email = user_regular.email

        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        response = self.app.post(
            route_path('edit_user_emails_add', user_id=user_id),
            params={'new_email': existing_email,
                    'csrf_token': self.csrf_token})
        assert_session_flash(
            response, 'This e-mail address is already taken')

        response = self.app.get(route_path('edit_user_emails', user_id=user_id))
        response.mustcontain(no=[existing_email])

    def test_emails_delete(self, user_util):
        self.log_user()
        user = user_util.create_user()
        user_id = user.user_id

        self.app.post(
            route_path('edit_user_emails_add', user_id=user_id),
            params={'new_email': 'example@rhodecode.com',
                    'csrf_token': self.csrf_token})

        response = self.app.get(route_path('edit_user_emails', user_id=user_id))
        response.mustcontain('example@rhodecode.com')

        user_email = UserEmailMap.query()\
            .filter(UserEmailMap.email == 'example@rhodecode.com') \
            .filter(UserEmailMap.user_id == user_id)\
            .one()

        del_email_id = user_email.email_id
        self.app.post(
            route_path('edit_user_emails_delete', user_id=user_id),
            params={'del_email_id': del_email_id,
                    'csrf_token': self.csrf_token})

        response = self.app.get(route_path('edit_user_emails', user_id=user_id))
        response.mustcontain(no=['example@rhodecode.com'])