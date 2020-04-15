# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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

from rhodecode.tests import assert_session_flash
from rhodecode.model.settings import SettingsModel


def route_path(name, params=None, **kwargs):
    import urllib
    from rhodecode.apps._base import ADMIN_PREFIX

    base_url = {
        'admin_defaults_repositories':
            ADMIN_PREFIX + '/defaults/repositories',
        'admin_defaults_repositories_update':
            ADMIN_PREFIX + '/defaults/repositories/update',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.usefixtures("app")
class TestDefaultsView(object):

    def test_index(self, autologin_user):
        response = self.app.get(route_path('admin_defaults_repositories'))
        response.mustcontain('default_repo_private')
        response.mustcontain('default_repo_enable_statistics')
        response.mustcontain('default_repo_enable_downloads')
        response.mustcontain('default_repo_enable_locking')

    def test_update_params_true_hg(self, autologin_user, csrf_token):
        params = {
            'default_repo_enable_locking': True,
            'default_repo_enable_downloads': True,
            'default_repo_enable_statistics': True,
            'default_repo_private': True,
            'default_repo_type': 'hg',
            'csrf_token': csrf_token,
        }
        response = self.app.post(
            route_path('admin_defaults_repositories_update'), params=params)
        assert_session_flash(response, 'Default settings updated successfully')

        defs = SettingsModel().get_default_repo_settings()
        del params['csrf_token']
        assert params == defs

    def test_update_params_false_git(self, autologin_user, csrf_token):
        params = {
            'default_repo_enable_locking': False,
            'default_repo_enable_downloads': False,
            'default_repo_enable_statistics': False,
            'default_repo_private': False,
            'default_repo_type': 'git',
            'csrf_token': csrf_token,
        }
        response = self.app.post(
            route_path('admin_defaults_repositories_update'), params=params)
        assert_session_flash(response, 'Default settings updated successfully')

        defs = SettingsModel().get_default_repo_settings()
        del params['csrf_token']
        assert params == defs
