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

from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.model.db import User, UserEmailMap
from rhodecode.tests import (
    TestController, TEST_USER_ADMIN_LOGIN, TEST_USER_REGULAR_EMAIL,
    assert_session_flash, TEST_USER_REGULAR_PASS)
from rhodecode.tests.fixture import Fixture

fixture = Fixture()


def route_path(name, **kwargs):
    return {
        'my_account_emails':
            ADMIN_PREFIX + '/my_account/emails',
        'my_account_emails_add':
            ADMIN_PREFIX + '/my_account/emails/new',
        'my_account_emails_delete':
            ADMIN_PREFIX + '/my_account/emails/delete',
    }[name].format(**kwargs)


class TestMyAccountEmails(TestController):
    def test_my_account_my_emails(self):
        self.log_user()
        response = self.app.get(route_path('my_account_emails'))
        response.mustcontain('No additional emails specified')

    def test_my_account_my_emails_add_remove(self):
        self.log_user()
        response = self.app.get(route_path('my_account_emails'))
        response.mustcontain('No additional emails specified')

        response = self.app.post(route_path('my_account_emails_add'),
                                 {'email': 'foo@barz.com',
                                  'current_password': TEST_USER_REGULAR_PASS,
                                  'csrf_token': self.csrf_token})

        response = self.app.get(route_path('my_account_emails'))

        email_id = UserEmailMap.query().filter(
            UserEmailMap.user == User.get_by_username(
                TEST_USER_ADMIN_LOGIN)).filter(
            UserEmailMap.email == 'foo@barz.com').one().email_id

        response.mustcontain('foo@barz.com')
        response.mustcontain('<input id="del_email_id" name="del_email_id" '
                             'type="hidden" value="%s" />' % email_id)

        response = self.app.post(
            route_path('my_account_emails_delete'), {
                'del_email_id': email_id,
                'csrf_token': self.csrf_token})
        assert_session_flash(response, 'Email successfully deleted')
        response = self.app.get(route_path('my_account_emails'))
        response.mustcontain('No additional emails specified')
