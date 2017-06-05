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

from rhodecode.lib import helpers as h
from rhodecode.model.db import User, UserFollowing, Repository
from rhodecode.tests import (
    TestController, url, TEST_USER_ADMIN_LOGIN, TEST_USER_REGULAR_EMAIL,
    assert_session_flash)
from rhodecode.tests.fixture import Fixture
from rhodecode.tests.utils import AssertResponse

fixture = Fixture()


def route_path(name, **kwargs):
    return {
        'home': '/',
    }[name].format(**kwargs)


class TestMyAccountController(TestController):
    test_user_1 = 'testme'
    test_user_1_password = '0jd83nHNS/d23n'
    destroy_users = set()

    @classmethod
    def teardown_class(cls):
        fixture.destroy_users(cls.destroy_users)

    def test_logout_form_contains_csrf(self, autologin_user, csrf_token):
        response = self.app.get(route_path('home'))
        assert_response = AssertResponse(response)
        element = assert_response.get_element('.logout #csrf_token')
        assert element.value == csrf_token

    def test_my_account_edit(self):
        self.log_user()
        response = self.app.get(url('my_account_edit'))

        response.mustcontain('value="test_admin')

    def test_my_account_my_repos(self):
        self.log_user()
        response = self.app.get(url('my_account_repos'))
        repos = Repository.query().filter(
            Repository.user == User.get_by_username(
                TEST_USER_ADMIN_LOGIN)).all()
        for repo in repos:
            response.mustcontain('"name_raw": "%s"' % repo.repo_name)

    def test_my_account_my_watched(self):
        self.log_user()
        response = self.app.get(url('my_account_watched'))

        repos = UserFollowing.query().filter(
            UserFollowing.user == User.get_by_username(
                TEST_USER_ADMIN_LOGIN)).all()
        for repo in repos:
            response.mustcontain(
                '"name_raw": "%s"' % repo.follows_repository.repo_name)

    @pytest.mark.backends("git", "hg")
    def test_my_account_my_pullrequests(self, pr_util):
        self.log_user()
        response = self.app.get(url('my_account_pullrequests'))
        response.mustcontain('There are currently no open pull '
                             'requests requiring your participation.')

        pr = pr_util.create_pull_request(title='TestMyAccountPR')
        response = self.app.get(url('my_account_pullrequests'))
        response.mustcontain('"name_raw": %s' % pr.pull_request_id)
        response.mustcontain('TestMyAccountPR')

    def test_my_account_my_emails(self):
        self.log_user()
        response = self.app.get(url('my_account_emails'))
        response.mustcontain('No additional emails specified')

    def test_my_account_my_emails_add_existing_email(self):
        self.log_user()
        response = self.app.get(url('my_account_emails'))
        response.mustcontain('No additional emails specified')
        response = self.app.post(url('my_account_emails'),
                                 {'new_email': TEST_USER_REGULAR_EMAIL,
                                  'csrf_token': self.csrf_token})
        assert_session_flash(response, 'This e-mail address is already taken')

    def test_my_account_my_emails_add_mising_email_in_form(self):
        self.log_user()
        response = self.app.get(url('my_account_emails'))
        response.mustcontain('No additional emails specified')
        response = self.app.post(url('my_account_emails'),
                                 {'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Please enter an email address')

    def test_my_account_my_emails_add_remove(self):
        self.log_user()
        response = self.app.get(url('my_account_emails'))
        response.mustcontain('No additional emails specified')

        response = self.app.post(url('my_account_emails'),
                                 {'new_email': 'foo@barz.com',
                                  'csrf_token': self.csrf_token})

        response = self.app.get(url('my_account_emails'))

        from rhodecode.model.db import UserEmailMap
        email_id = UserEmailMap.query().filter(
            UserEmailMap.user == User.get_by_username(
                TEST_USER_ADMIN_LOGIN)).filter(
                    UserEmailMap.email == 'foo@barz.com').one().email_id

        response.mustcontain('foo@barz.com')
        response.mustcontain('<input id="del_email_id" name="del_email_id" '
                             'type="hidden" value="%s" />' % email_id)

        response = self.app.post(
            url('my_account_emails'), {
                'del_email_id': email_id, '_method': 'delete',
                'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Removed email address from user account')
        response = self.app.get(url('my_account_emails'))
        response.mustcontain('No additional emails specified')

    @pytest.mark.parametrize(
        "name, attrs", [
            ('firstname', {'firstname': 'new_username'}),
            ('lastname', {'lastname': 'new_username'}),
            ('admin', {'admin': True}),
            ('admin', {'admin': False}),
            ('extern_type', {'extern_type': 'ldap'}),
            ('extern_type', {'extern_type': None}),
            # ('extern_name', {'extern_name': 'test'}),
            # ('extern_name', {'extern_name': None}),
            ('active', {'active': False}),
            ('active', {'active': True}),
            ('email', {'email': 'some@email.com'}),
        ])
    def test_my_account_update(self, name, attrs):
        usr = fixture.create_user(self.test_user_1,
                                  password=self.test_user_1_password,
                                  email='testme@rhodecode.org',
                                  extern_type='rhodecode',
                                  extern_name=self.test_user_1,
                                  skip_if_exists=True)
        self.destroy_users.add(self.test_user_1)

        params = usr.get_api_data()  # current user data
        user_id = usr.user_id
        self.log_user(
            username=self.test_user_1, password=self.test_user_1_password)

        params.update({'password_confirmation': ''})
        params.update({'new_password': ''})
        params.update({'extern_type': 'rhodecode'})
        params.update({'extern_name': self.test_user_1})
        params.update({'csrf_token': self.csrf_token})

        params.update(attrs)
        # my account page cannot set language param yet, only for admins
        del params['language']
        response = self.app.post(url('my_account'), params)

        assert_session_flash(
            response, 'Your account was updated successfully')

        del params['csrf_token']

        updated_user = User.get_by_username(self.test_user_1)
        updated_params = updated_user.get_api_data()
        updated_params.update({'password_confirmation': ''})
        updated_params.update({'new_password': ''})

        params['last_login'] = updated_params['last_login']
        params['last_activity'] = updated_params['last_activity']
        # my account page cannot set language param yet, only for admins
        # but we get this info from API anyway
        params['language'] = updated_params['language']

        if name == 'email':
            params['emails'] = [attrs['email']]
        if name == 'extern_type':
            # cannot update this via form, expected value is original one
            params['extern_type'] = "rhodecode"
        if name == 'extern_name':
            # cannot update this via form, expected value is original one
            params['extern_name'] = str(user_id)
        if name == 'active':
            # my account cannot deactivate account
            params['active'] = True
        if name == 'admin':
            # my account cannot make you an admin !
            params['admin'] = False

        assert params == updated_params

    def test_my_account_update_err_email_exists(self):
        self.log_user()

        new_email = 'test_regular@mail.com'  # already exisitn email
        response = self.app.post(url('my_account'),
                                 params={
                                     'username': 'test_admin',
                                     'new_password': 'test12',
                                     'password_confirmation': 'test122',
                                     'firstname': 'NewName',
                                     'lastname': 'NewLastname',
                                     'email': new_email,
                                     'csrf_token': self.csrf_token,
            })

        response.mustcontain('This e-mail address is already taken')

    def test_my_account_update_err(self):
        self.log_user('test_regular2', 'test12')

        new_email = 'newmail.pl'
        response = self.app.post(url('my_account'),
                                 params={
                                     'username': 'test_admin',
                                     'new_password': 'test12',
                                     'password_confirmation': 'test122',
                                     'firstname': 'NewName',
                                     'lastname': 'NewLastname',
                                     'email': new_email,
                                     'csrf_token': self.csrf_token,
            })

        response.mustcontain('An email address must contain a single @')
        from rhodecode.model import validators
        msg = validators.ValidUsername(
            edit=False, old_data={})._messages['username_exists']
        msg = h.html_escape(msg % {'username': 'test_admin'})
        response.mustcontain(u"%s" % msg)
