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

import urlparse

import mock
import pytest

from rhodecode.tests import (
    assert_session_flash, HG_REPO, TEST_USER_ADMIN_LOGIN,
    no_newline_id_generator)
from rhodecode.tests.fixture import Fixture
from rhodecode.lib.auth import check_password
from rhodecode.lib import helpers as h
from rhodecode.model.auth_token import AuthTokenModel
from rhodecode.model.db import User, Notification, UserApiKeys
from rhodecode.model.meta import Session

fixture = Fixture()

whitelist_view = ['RepoCommitsView:repo_commit_raw']


def route_path(name, params=None, **kwargs):
    import urllib
    from rhodecode.apps._base import ADMIN_PREFIX

    base_url = {
        'login': ADMIN_PREFIX + '/login',
        'logout': ADMIN_PREFIX + '/logout',
        'register': ADMIN_PREFIX + '/register',
        'reset_password':
            ADMIN_PREFIX + '/password_reset',
        'reset_password_confirmation':
            ADMIN_PREFIX + '/password_reset_confirmation',

        'admin_permissions_application':
            ADMIN_PREFIX + '/permissions/application',
        'admin_permissions_application_update':
            ADMIN_PREFIX + '/permissions/application/update',

        'repo_commit_raw': '/{repo_name}/raw-changeset/{commit_id}'

    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.usefixtures('app')
class TestLoginController(object):
    destroy_users = set()

    @classmethod
    def teardown_class(cls):
        fixture.destroy_users(cls.destroy_users)

    def teardown_method(self, method):
        for n in Notification.query().all():
            Session().delete(n)

        Session().commit()
        assert Notification.query().all() == []

    def test_index(self):
        response = self.app.get(route_path('login'))
        assert response.status == '200 OK'
        # Test response...

    def test_login_admin_ok(self):
        response = self.app.post(route_path('login'),
                                 {'username': 'test_admin',
                                  'password': 'test12'}, status=302)
        response = response.follow()
        session = response.get_session_from_response()
        username = session['rhodecode_user'].get('username')
        assert username == 'test_admin'
        response.mustcontain('/%s' % HG_REPO)

    def test_login_regular_ok(self):
        response = self.app.post(route_path('login'),
                                 {'username': 'test_regular',
                                  'password': 'test12'}, status=302)

        response = response.follow()
        session = response.get_session_from_response()
        username = session['rhodecode_user'].get('username')
        assert username == 'test_regular'

        response.mustcontain('/%s' % HG_REPO)

    def test_login_ok_came_from(self):
        test_came_from = '/_admin/users?branch=stable'
        _url = '{}?came_from={}'.format(route_path('login'), test_came_from)
        response = self.app.post(
            _url, {'username': 'test_admin', 'password': 'test12'}, status=302)

        assert 'branch=stable' in response.location
        response = response.follow()

        assert response.status == '200 OK'
        response.mustcontain('Users administration')

    def test_redirect_to_login_with_get_args(self):
        with fixture.anon_access(False):
            kwargs = {'branch': 'stable'}
            response = self.app.get(
                h.route_path('repo_summary', repo_name=HG_REPO, _query=kwargs),
                status=302)

            response_query = urlparse.parse_qsl(response.location)
            assert 'branch=stable' in response_query[0][1]

    def test_login_form_with_get_args(self):
        _url = '{}?came_from=/_admin/users,branch=stable'.format(route_path('login'))
        response = self.app.get(_url)
        assert 'branch%3Dstable' in response.form.action

    @pytest.mark.parametrize("url_came_from", [
        'data:text/html,<script>window.alert("xss")</script>',
        'mailto:test@rhodecode.org',
        'file:///etc/passwd',
        'ftp://some.ftp.server',
        'http://other.domain',
        '/\r\nX-Forwarded-Host: http://example.org',
    ], ids=no_newline_id_generator)
    def test_login_bad_came_froms(self, url_came_from):
        _url = '{}?came_from={}'.format(route_path('login'), url_came_from)
        response = self.app.post(
            _url,
            {'username': 'test_admin', 'password': 'test12'})
        assert response.status == '302 Found'
        response = response.follow()
        assert response.status == '200 OK'
        assert response.request.path == '/'

    def test_login_short_password(self):
        response = self.app.post(route_path('login'),
                                 {'username': 'test_admin',
                                  'password': 'as'})
        assert response.status == '200 OK'

        response.mustcontain('Enter 3 characters or more')

    def test_login_wrong_non_ascii_password(self, user_regular):
        response = self.app.post(
            route_path('login'),
            {'username': user_regular.username,
             'password': u'invalid-non-asci\xe4'.encode('utf8')})

        response.mustcontain('invalid user name')
        response.mustcontain('invalid password')

    def test_login_with_non_ascii_password(self, user_util):
        password = u'valid-non-ascii\xe4'
        user = user_util.create_user(password=password)
        response = self.app.post(
            route_path('login'),
            {'username': user.username,
             'password': password.encode('utf-8')})
        assert response.status_code == 302

    def test_login_wrong_username_password(self):
        response = self.app.post(route_path('login'),
                                 {'username': 'error',
                                  'password': 'test12'})

        response.mustcontain('invalid user name')
        response.mustcontain('invalid password')

    def test_login_admin_ok_password_migration(self, real_crypto_backend):
        from rhodecode.lib import auth

        # create new user, with sha256 password
        temp_user = 'test_admin_sha256'
        user = fixture.create_user(temp_user)
        user.password = auth._RhodeCodeCryptoSha256().hash_create(
            b'test123')
        Session().add(user)
        Session().commit()
        self.destroy_users.add(temp_user)
        response = self.app.post(route_path('login'),
                                 {'username': temp_user,
                                  'password': 'test123'}, status=302)

        response = response.follow()
        session = response.get_session_from_response()
        username = session['rhodecode_user'].get('username')
        assert username == temp_user
        response.mustcontain('/%s' % HG_REPO)

        # new password should be bcrypted, after log-in and transfer
        user = User.get_by_username(temp_user)
        assert user.password.startswith('$')

    # REGISTRATIONS
    def test_register(self):
        response = self.app.get(route_path('register'))
        response.mustcontain('Create an Account')

    def test_register_err_same_username(self):
        uname = 'test_admin'
        response = self.app.post(
            route_path('register'),
            {
                'username': uname,
                'password': 'test12',
                'password_confirmation': 'test12',
                'email': 'goodmail@domain.com',
                'firstname': 'test',
                'lastname': 'test'
            }
        )

        assertr = response.assert_response()
        msg = 'Username "%(username)s" already exists'
        msg = msg % {'username': uname}
        assertr.element_contains('#username+.error-message', msg)

    def test_register_err_same_email(self):
        response = self.app.post(
            route_path('register'),
            {
                'username': 'test_admin_0',
                'password': 'test12',
                'password_confirmation': 'test12',
                'email': 'test_admin@mail.com',
                'firstname': 'test',
                'lastname': 'test'
            }
        )

        assertr = response.assert_response()
        msg = u'This e-mail address is already taken'
        assertr.element_contains('#email+.error-message', msg)

    def test_register_err_same_email_case_sensitive(self):
        response = self.app.post(
            route_path('register'),
            {
                'username': 'test_admin_1',
                'password': 'test12',
                'password_confirmation': 'test12',
                'email': 'TesT_Admin@mail.COM',
                'firstname': 'test',
                'lastname': 'test'
            }
        )
        assertr = response.assert_response()
        msg = u'This e-mail address is already taken'
        assertr.element_contains('#email+.error-message', msg)

    def test_register_err_wrong_data(self):
        response = self.app.post(
            route_path('register'),
            {
                'username': 'xs',
                'password': 'test',
                'password_confirmation': 'test',
                'email': 'goodmailm',
                'firstname': 'test',
                'lastname': 'test'
            }
        )
        assert response.status == '200 OK'
        response.mustcontain('An email address must contain a single @')
        response.mustcontain('Enter a value 6 characters long or more')

    def test_register_err_username(self):
        response = self.app.post(
            route_path('register'),
            {
                'username': 'error user',
                'password': 'test12',
                'password_confirmation': 'test12',
                'email': 'goodmailm',
                'firstname': 'test',
                'lastname': 'test'
            }
        )

        response.mustcontain('An email address must contain a single @')
        response.mustcontain(
            'Username may only contain '
            'alphanumeric characters underscores, '
            'periods or dashes and must begin with '
            'alphanumeric character')

    def test_register_err_case_sensitive(self):
        usr = 'Test_Admin'
        response = self.app.post(
            route_path('register'),
            {
                'username': usr,
                'password': 'test12',
                'password_confirmation': 'test12',
                'email': 'goodmailm',
                'firstname': 'test',
                'lastname': 'test'
            }
        )

        assertr = response.assert_response()
        msg = u'Username "%(username)s" already exists'
        msg = msg % {'username': usr}
        assertr.element_contains('#username+.error-message', msg)

    def test_register_special_chars(self):
        response = self.app.post(
            route_path('register'),
            {
                'username': 'xxxaxn',
                'password': 'ąćźżąśśśś',
                'password_confirmation': 'ąćźżąśśśś',
                'email': 'goodmailm@test.plx',
                'firstname': 'test',
                'lastname': 'test'
            }
        )

        msg = u'Invalid characters (non-ascii) in password'
        response.mustcontain(msg)

    def test_register_password_mismatch(self):
        response = self.app.post(
            route_path('register'),
            {
                'username': 'xs',
                'password': '123qwe',
                'password_confirmation': 'qwe123',
                'email': 'goodmailm@test.plxa',
                'firstname': 'test',
                'lastname': 'test'
            }
        )
        msg = u'Passwords do not match'
        response.mustcontain(msg)

    def test_register_ok(self):
        username = 'test_regular4'
        password = 'qweqwe'
        email = 'marcin@test.com'
        name = 'testname'
        lastname = 'testlastname'

        # this initializes a session
        response = self.app.get(route_path('register'))
        response.mustcontain('Create an Account')


        response = self.app.post(
            route_path('register'),
            {
                'username': username,
                'password': password,
                'password_confirmation': password,
                'email': email,
                'firstname': name,
                'lastname': lastname,
                'admin': True
            },
            status=302
        )  # This should be overridden

        assert_session_flash(
            response, 'You have successfully registered with RhodeCode')

        ret = Session().query(User).filter(
            User.username == 'test_regular4').one()
        assert ret.username == username
        assert check_password(password, ret.password)
        assert ret.email == email
        assert ret.name == name
        assert ret.lastname == lastname
        assert ret.auth_tokens is not None
        assert not ret.admin

    def test_forgot_password_wrong_mail(self):
        bad_email = 'marcin@wrongmail.org'
        # this initializes a session
        self.app.get(route_path('reset_password'))

        response = self.app.post(
            route_path('reset_password'), {'email': bad_email, }
        )
        assert_session_flash(response,
            'If such email exists, a password reset link was sent to it.')

    def test_forgot_password(self, user_util):
        # this initializes a session
        self.app.get(route_path('reset_password'))

        user = user_util.create_user()
        user_id = user.user_id
        email = user.email

        response = self.app.post(route_path('reset_password'), {'email': email, })

        assert_session_flash(response,
            'If such email exists, a password reset link was sent to it.')

        # BAD KEY
        confirm_url = '{}?key={}'.format(route_path('reset_password_confirmation'), 'badkey')
        response = self.app.get(confirm_url, status=302)
        assert response.location.endswith(route_path('reset_password'))
        assert_session_flash(response, 'Given reset token is invalid')

        response.follow()  # cleanup flash

        # GOOD KEY
        key = UserApiKeys.query()\
            .filter(UserApiKeys.user_id == user_id)\
            .filter(UserApiKeys.role == UserApiKeys.ROLE_PASSWORD_RESET)\
            .first()

        assert key

        confirm_url = '{}?key={}'.format(route_path('reset_password_confirmation'), key.api_key)
        response = self.app.get(confirm_url)
        assert response.status == '302 Found'
        assert response.location.endswith(route_path('login'))

        assert_session_flash(
            response,
            'Your password reset was successful, '
            'a new password has been sent to your email')

        response.follow()

    def _get_api_whitelist(self, values=None):
        config = {'api_access_controllers_whitelist': values or []}
        return config

    @pytest.mark.parametrize("test_name, auth_token", [
        ('none', None),
        ('empty_string', ''),
        ('fake_number', '123456'),
        ('proper_auth_token', None)
    ])
    def test_access_not_whitelisted_page_via_auth_token(
            self, test_name, auth_token, user_admin):

        whitelist = self._get_api_whitelist([])
        with mock.patch.dict('rhodecode.CONFIG', whitelist):
            assert [] == whitelist['api_access_controllers_whitelist']
            if test_name == 'proper_auth_token':
                # use builtin if api_key is None
                auth_token = user_admin.api_key

            with fixture.anon_access(False):
                self.app.get(
                    route_path('repo_commit_raw',
                               repo_name=HG_REPO, commit_id='tip',
                               params=dict(api_key=auth_token)),
                    status=302)

    @pytest.mark.parametrize("test_name, auth_token, code", [
        ('none', None, 302),
        ('empty_string', '', 302),
        ('fake_number', '123456', 302),
        ('proper_auth_token', None, 200)
    ])
    def test_access_whitelisted_page_via_auth_token(
            self, test_name, auth_token, code, user_admin):

        whitelist = self._get_api_whitelist(whitelist_view)

        with mock.patch.dict('rhodecode.CONFIG', whitelist):
            assert whitelist_view == whitelist['api_access_controllers_whitelist']

            if test_name == 'proper_auth_token':
                auth_token = user_admin.api_key
                assert auth_token

            with fixture.anon_access(False):
                self.app.get(
                    route_path('repo_commit_raw',
                               repo_name=HG_REPO, commit_id='tip',
                               params=dict(api_key=auth_token)),
                    status=code)

    @pytest.mark.parametrize("test_name, auth_token, code", [
        ('proper_auth_token', None, 200),
        ('wrong_auth_token', '123456', 302),
    ])
    def test_access_whitelisted_page_via_auth_token_bound_to_token(
            self, test_name, auth_token, code, user_admin):

        expected_token = auth_token
        if test_name == 'proper_auth_token':
            auth_token = user_admin.api_key
            expected_token = auth_token
            assert auth_token

        whitelist = self._get_api_whitelist([
            'RepoCommitsView:repo_commit_raw@{}'.format(expected_token)])

        with mock.patch.dict('rhodecode.CONFIG', whitelist):

            with fixture.anon_access(False):
                self.app.get(
                    route_path('repo_commit_raw',
                               repo_name=HG_REPO, commit_id='tip',
                               params=dict(api_key=auth_token)),
                    status=code)

    def test_access_page_via_extra_auth_token(self):
        whitelist = self._get_api_whitelist(whitelist_view)
        with mock.patch.dict('rhodecode.CONFIG', whitelist):
            assert whitelist_view == \
                whitelist['api_access_controllers_whitelist']

            new_auth_token = AuthTokenModel().create(
                TEST_USER_ADMIN_LOGIN, 'test')
            Session().commit()
            with fixture.anon_access(False):
                self.app.get(
                    route_path('repo_commit_raw',
                               repo_name=HG_REPO, commit_id='tip',
                               params=dict(api_key=new_auth_token.api_key)),
                    status=200)

    def test_access_page_via_expired_auth_token(self):
        whitelist = self._get_api_whitelist(whitelist_view)
        with mock.patch.dict('rhodecode.CONFIG', whitelist):
            assert whitelist_view == \
                whitelist['api_access_controllers_whitelist']

            new_auth_token = AuthTokenModel().create(
                TEST_USER_ADMIN_LOGIN, 'test')
            Session().commit()
            # patch the api key and make it expired
            new_auth_token.expires = 0
            Session().add(new_auth_token)
            Session().commit()
            with fixture.anon_access(False):
                self.app.get(
                    route_path('repo_commit_raw',
                               repo_name=HG_REPO, commit_id='tip',
                               params=dict(api_key=new_auth_token.api_key)),
                    status=302)
