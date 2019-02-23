# -*- coding: utf-8 -*-

# Copyright (C) 2016-2019 RhodeCode GmbH
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
# -*- coding: utf-8 -*-

# Copyright (C) 2016-2019 RhodeCode GmbH
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

from rhodecode.model.db import User
from rhodecode.tests import TestController, assert_session_flash
from rhodecode.lib import helpers as h


def route_path(name, params=None, **kwargs):
    import urllib
    from rhodecode.apps._base import ADMIN_PREFIX

    base_url = {
        'my_account_edit': ADMIN_PREFIX + '/my_account/edit',
        'my_account_update': ADMIN_PREFIX + '/my_account/update',
        'my_account_pullrequests': ADMIN_PREFIX + '/my_account/pull_requests',
        'my_account_pullrequests_data': ADMIN_PREFIX + '/my_account/pull_requests/data',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestMyAccountEdit(TestController):

    def test_my_account_edit(self):
        self.log_user()
        response = self.app.get(route_path('my_account_edit'))

        response.mustcontain('value="test_admin')

    @pytest.mark.backends("git", "hg")
    def test_my_account_my_pullrequests(self, pr_util):
        self.log_user()
        response = self.app.get(route_path('my_account_pullrequests'))
        response.mustcontain('There are currently no open pull '
                             'requests requiring your participation.')

    @pytest.mark.backends("git", "hg")
    def test_my_account_my_pullrequests_data(self, pr_util, xhr_header):
        self.log_user()
        response = self.app.get(route_path('my_account_pullrequests_data'),
                                extra_environ=xhr_header)
        assert response.json == {
            u'data': [], u'draw': None,
            u'recordsFiltered': 0, u'recordsTotal': 0}

        pr = pr_util.create_pull_request(title='TestMyAccountPR')
        expected = {
            'author_raw': 'RhodeCode Admin',
            'name_raw': pr.pull_request_id
        }
        response = self.app.get(route_path('my_account_pullrequests_data'),
                                extra_environ=xhr_header)
        assert response.json['recordsTotal'] == 1
        assert response.json['data'][0]['author_raw'] == expected['author_raw']

        assert response.json['data'][0]['author_raw'] == expected['author_raw']
        assert response.json['data'][0]['name_raw'] == expected['name_raw']

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
            ('email', {'email': u'some@email.com'}),
        ])
    def test_my_account_update(self, name, attrs, user_util):
        usr = user_util.create_user(password='qweqwe')
        params = usr.get_api_data()  # current user data
        user_id = usr.user_id
        self.log_user(
            username=usr.username, password='qweqwe')

        params.update({'password_confirmation': ''})
        params.update({'new_password': ''})
        params.update({'extern_type': u'rhodecode'})
        params.update({'extern_name': u'rhodecode'})
        params.update({'csrf_token': self.csrf_token})

        params.update(attrs)
        # my account page cannot set language param yet, only for admins
        del params['language']
        if name == 'email':
            uem = user_util.create_additional_user_email(usr, attrs['email'])
            email_before = User.get(user_id).email

        response = self.app.post(route_path('my_account_update'), params)

        assert_session_flash(
            response, 'Your account was updated successfully')

        del params['csrf_token']

        updated_user = User.get(user_id)
        updated_params = updated_user.get_api_data()
        updated_params.update({'password_confirmation': ''})
        updated_params.update({'new_password': ''})

        params['last_login'] = updated_params['last_login']
        params['last_activity'] = updated_params['last_activity']
        # my account page cannot set language param yet, only for admins
        # but we get this info from API anyway
        params['language'] = updated_params['language']

        if name == 'email':
            params['emails'] = [attrs['email'], email_before]
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

    def test_my_account_update_err_email_not_exists_in_emails(self):
        self.log_user()

        new_email = 'test_regular@mail.com'  # not in emails
        params = {
            'username': 'test_admin',
            'new_password': 'test12',
            'password_confirmation': 'test122',
            'firstname': 'NewName',
            'lastname': 'NewLastname',
            'email': new_email,
            'csrf_token': self.csrf_token,
        }

        response = self.app.post(route_path('my_account_update'),
                                 params=params)

        response.mustcontain('"test_regular@mail.com" is not one of test_admin@mail.com')

    def test_my_account_update_bad_email_address(self):
        self.log_user('test_regular2', 'test12')

        new_email = 'newmail.pl'
        params = {
            'username': 'test_admin',
            'new_password': 'test12',
            'password_confirmation': 'test122',
            'firstname': 'NewName',
            'lastname': 'NewLastname',
            'email': new_email,
            'csrf_token': self.csrf_token,
        }
        response = self.app.post(route_path('my_account_update'),
                                 params=params)

        response.mustcontain('"newmail.pl" is not one of test_regular2@mail.com')
