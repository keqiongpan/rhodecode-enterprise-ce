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

import mock
import pytest

import rhodecode
from rhodecode.model.db import Repository
from rhodecode.model.settings import SettingsModel
from rhodecode.tests.utils import AssertResponse


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'edit_repo': '/{repo_name}/settings',
        'edit_repo_vcs': '/{repo_name}/settings/vcs',
        'edit_repo_vcs_update': '/{repo_name}/settings/vcs/update',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.usefixtures('autologin_user', 'app')
class TestAdminRepoVcsSettings(object):

    @pytest.mark.parametrize('setting_name, setting_backends', [
        ('hg_use_rebase_for_merging', ['hg']),
    ])
    def test_labs_settings_visible_if_enabled(
            self, setting_name, setting_backends, backend):
        if backend.alias not in setting_backends:
            pytest.skip('Setting not available for backend {}'.format(backend))

        vcs_settings_url = route_path(
            'edit_repo_vcs', repo_name=backend.repo.repo_name)

        with mock.patch.dict(
                rhodecode.CONFIG, {'labs_settings_active': 'true'}):
            response = self.app.get(vcs_settings_url)

        assertr = response.assert_response()
        assertr.one_element_exists('#rhodecode_{}'.format(setting_name))

    @pytest.mark.parametrize('setting_name, setting_backends', [
        ('hg_use_rebase_for_merging', ['hg']),
    ])
    def test_update_boolean_settings(
            self, csrf_token, setting_name, setting_backends, backend):
        if backend.alias not in setting_backends:
            pytest.skip('Setting not available for backend {}'.format(backend))

        repo = backend.create_repo()
        repo_name = repo.repo_name

        settings_model = SettingsModel(repo=repo)
        vcs_settings_url = route_path(
            'edit_repo_vcs_update', repo_name=repo_name)

        self.app.post(
            vcs_settings_url,
            params={
                'inherit_global_settings': False,
                'new_svn_branch': 'dummy-value-for-testing',
                'new_svn_tag': 'dummy-value-for-testing',
                'rhodecode_{}'.format(setting_name): 'true',
                'csrf_token': csrf_token,
            })
        settings_model = SettingsModel(repo=Repository.get_by_repo_name(repo_name))
        setting = settings_model.get_setting_by_name(setting_name)
        assert setting.app_settings_value

        self.app.post(
            vcs_settings_url,
            params={
                'inherit_global_settings': False,
                'new_svn_branch': 'dummy-value-for-testing',
                'new_svn_tag': 'dummy-value-for-testing',
                'rhodecode_{}'.format(setting_name): 'false',
                'csrf_token': csrf_token,
            })
        settings_model = SettingsModel(repo=Repository.get_by_repo_name(repo_name))
        setting = settings_model.get_setting_by_name(setting_name)
        assert not setting.app_settings_value
