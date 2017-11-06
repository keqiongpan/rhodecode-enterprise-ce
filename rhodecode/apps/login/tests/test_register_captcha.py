# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 RhodeCode GmbH
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

from rhodecode.apps.login.views import LoginView, CaptchaData
from rhodecode.config.routing import ADMIN_PREFIX
from rhodecode.lib.utils2 import AttributeDict
from rhodecode.model.settings import SettingsModel
from rhodecode.tests.utils import AssertResponse


class RhodeCodeSetting(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __enter__(self):
        from rhodecode.model.settings import SettingsModel
        model = SettingsModel()
        self.old_setting = model.get_setting_by_name(self.name)
        model.create_or_update_setting(name=self.name, val=self.value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        model = SettingsModel()
        if self.old_setting:
            model.create_or_update_setting(
                name=self.name, val=self.old_setting.app_settings_value)
        else:
            model.create_or_update_setting(name=self.name)


class TestRegisterCaptcha(object):

    @pytest.mark.parametrize('private_key, public_key, expected', [
        ('',        '',       CaptchaData(False, '',        '')),
        ('',        'pubkey', CaptchaData(False, '',        'pubkey')),
        ('privkey', '',       CaptchaData(True,  'privkey', '')),
        ('privkey', 'pubkey', CaptchaData(True,  'privkey', 'pubkey')),
    ])
    def test_get_captcha_data(self, private_key, public_key, expected, db,
                              request_stub, user_util):
        request_stub.user = user_util.create_user().AuthUser()
        request_stub.matched_route = AttributeDict({'name': 'login'})
        login_view = LoginView(mock.Mock(), request_stub)

        with RhodeCodeSetting('captcha_private_key', private_key):
            with RhodeCodeSetting('captcha_public_key', public_key):
                captcha = login_view._get_captcha_data()
                assert captcha == expected

    @pytest.mark.parametrize('active', [False, True])
    @mock.patch.object(LoginView, '_get_captcha_data')
    def test_private_key_does_not_leak_to_html(
            self, m_get_captcha_data, active, app):
        captcha = CaptchaData(
            active=active, private_key='PRIVATE_KEY', public_key='PUBLIC_KEY')
        m_get_captcha_data.return_value = captcha

        response = app.get(ADMIN_PREFIX + '/register')
        assert 'PRIVATE_KEY' not in response

    @pytest.mark.parametrize('active', [False, True])
    @mock.patch.object(LoginView, '_get_captcha_data')
    def test_register_view_renders_captcha(
            self, m_get_captcha_data, active, app):
        captcha = CaptchaData(
            active=active, private_key='PRIVATE_KEY', public_key='PUBLIC_KEY')
        m_get_captcha_data.return_value = captcha

        response = app.get(ADMIN_PREFIX + '/register')

        assertr = AssertResponse(response)
        if active:
            assertr.one_element_exists('#recaptcha_field')
        else:
            assertr.no_element_exists('#recaptcha_field')

    @pytest.mark.parametrize('valid', [False, True])
    @mock.patch('rhodecode.apps.login.views.submit')
    @mock.patch.object(LoginView, '_get_captcha_data')
    def test_register_with_active_captcha(
            self, m_get_captcha_data, m_submit, valid, app, csrf_token):
        captcha = CaptchaData(
            active=True, private_key='PRIVATE_KEY', public_key='PUBLIC_KEY')
        m_get_captcha_data.return_value = captcha
        m_response = mock.Mock()
        m_response.is_valid = valid
        m_submit.return_value = m_response

        params = {
            'csrf_token': csrf_token,
            'email': 'pytest@example.com',
            'firstname': 'pytest-firstname',
            'lastname': 'pytest-lastname',
            'password': 'secret',
            'password_confirmation': 'secret',
            'username': 'pytest',
        }
        response = app.post(ADMIN_PREFIX + '/register', params=params)

        if valid:
            # If we provided a valid captcha input we expect a successful
            # registration and redirect to the login page.
            assert response.status_int == 302
            assert 'location' in response.headers
            assert ADMIN_PREFIX + '/login' in response.headers['location']
        else:
            # If captche input is invalid we expect to stay on the registration
            # page with an error message displayed.
            assertr = AssertResponse(response)
            assert response.status_int == 200
            assertr.one_element_exists('#recaptcha_field ~ span.error-message')
