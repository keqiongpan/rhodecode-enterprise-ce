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

import mock
import pytest

from rhodecode.lib import auth
from rhodecode.lib.utils2 import str2bool
from rhodecode.model.db import (
    Repository, UserRepoToPerm, User)
from rhodecode.model.meta import Session
from rhodecode.model.settings import SettingsModel, VcsSettingsModel
from rhodecode.model.user import UserModel
from rhodecode.tests import (
    login_user_session, logout_user_session,
    TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
from rhodecode.tests.fixture import Fixture
from rhodecode.tests.utils import AssertResponse

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'repo_summary': '/{repo_name}',
        'repo_creating_check': '/{repo_name}/repo_creating_check',
        'edit_repo': '/{repo_name}/settings',
        'edit_repo_vcs': '/{repo_name}/settings/vcs',
        'edit_repo_vcs_update': '/{repo_name}/settings/vcs/update',
        'edit_repo_vcs_svn_pattern_delete': '/{repo_name}/settings/vcs/svn_pattern/delete'
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.usefixtures("app")
class TestVcsSettings(object):
    FORM_DATA = {
        'inherit_global_settings': False,
        'hooks_changegroup_repo_size': False,
        'hooks_changegroup_push_logger': False,
        'hooks_outgoing_pull_logger': False,
        'extensions_largefiles': False,
        'extensions_evolve': False,
        'phases_publish': 'False',
        'rhodecode_pr_merge_enabled': False,
        'rhodecode_use_outdated_comments': False,
        'new_svn_branch': '',
        'new_svn_tag': ''
    }

    @pytest.mark.skip_backends('svn')
    def test_global_settings_initial_values(self, autologin_user, backend):
        repo_name = backend.repo_name
        response = self.app.get(route_path('edit_repo_vcs', repo_name=repo_name))

        expected_settings = (
            'rhodecode_use_outdated_comments', 'rhodecode_pr_merge_enabled',
            'hooks_changegroup_repo_size', 'hooks_changegroup_push_logger',
            'hooks_outgoing_pull_logger'
        )
        for setting in expected_settings:
            self.assert_repo_value_equals_global_value(response, setting)

    def test_show_settings_requires_repo_admin_permission(
            self, backend, user_util, settings_util):
        repo = backend.create_repo()
        repo_name = repo.repo_name
        user = UserModel().get_by_username(TEST_USER_REGULAR_LOGIN)
        user_util.grant_user_permission_to_repo(repo, user, 'repository.admin')
        login_user_session(
            self.app, TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        self.app.get(route_path('edit_repo_vcs', repo_name=repo_name), status=200)

    def test_inherit_global_settings_flag_is_true_by_default(
            self, autologin_user, backend):
        repo_name = backend.repo_name
        response = self.app.get(route_path('edit_repo_vcs', repo_name=repo_name))

        assert_response = AssertResponse(response)
        element = assert_response.get_element('#inherit_global_settings')
        assert element.checked

    @pytest.mark.parametrize('checked_value', [True, False])
    def test_inherit_global_settings_value(
            self, autologin_user, backend, checked_value, settings_util):
        repo = backend.create_repo()
        repo_name = repo.repo_name
        settings_util.create_repo_rhodecode_setting(
            repo, 'inherit_vcs_settings', checked_value, 'bool')
        response = self.app.get(route_path('edit_repo_vcs', repo_name=repo_name))

        assert_response = AssertResponse(response)
        element = assert_response.get_element('#inherit_global_settings')
        assert element.checked == checked_value

    @pytest.mark.skip_backends('svn')
    def test_hooks_settings_are_created(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.repo_name
        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        settings = SettingsModel(repo=repo_name)
        try:
            for section, key in VcsSettingsModel.HOOKS_SETTINGS:
                ui = settings.get_ui_by_section_and_key(section, key)
                assert ui.ui_active is False
        finally:
            self._cleanup_repo_settings(settings)

    def test_hooks_settings_are_not_created_for_svn(
            self, autologin_user, backend_svn, csrf_token):
        repo_name = backend_svn.repo_name
        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        settings = SettingsModel(repo=repo_name)
        try:
            for section, key in VcsSettingsModel.HOOKS_SETTINGS:
                ui = settings.get_ui_by_section_and_key(section, key)
                assert ui is None
        finally:
            self._cleanup_repo_settings(settings)

    @pytest.mark.skip_backends('svn')
    def test_hooks_settings_are_updated(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.repo_name
        settings = SettingsModel(repo=repo_name)
        for section, key in VcsSettingsModel.HOOKS_SETTINGS:
            settings.create_ui_section_value(section, '', key=key, active=True)

        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        try:
            for section, key in VcsSettingsModel.HOOKS_SETTINGS:
                ui = settings.get_ui_by_section_and_key(section, key)
                assert ui.ui_active is False
        finally:
            self._cleanup_repo_settings(settings)

    def test_hooks_settings_are_not_updated_for_svn(
            self, autologin_user, backend_svn, csrf_token):
        repo_name = backend_svn.repo_name
        settings = SettingsModel(repo=repo_name)
        for section, key in VcsSettingsModel.HOOKS_SETTINGS:
            settings.create_ui_section_value(section, '', key=key, active=True)

        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        try:
            for section, key in VcsSettingsModel.HOOKS_SETTINGS:
                ui = settings.get_ui_by_section_and_key(section, key)
                assert ui.ui_active is True
        finally:
            self._cleanup_repo_settings(settings)

    @pytest.mark.skip_backends('svn')
    def test_pr_settings_are_created(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.repo_name
        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        settings = SettingsModel(repo=repo_name)
        try:
            for name in VcsSettingsModel.GENERAL_SETTINGS:
                setting = settings.get_setting_by_name(name)
                assert setting.app_settings_value is False
        finally:
            self._cleanup_repo_settings(settings)

    def test_pr_settings_are_not_created_for_svn(
            self, autologin_user, backend_svn, csrf_token):
        repo_name = backend_svn.repo_name
        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        settings = SettingsModel(repo=repo_name)
        try:
            for name in VcsSettingsModel.GENERAL_SETTINGS:
                setting = settings.get_setting_by_name(name)
                assert setting is None
        finally:
            self._cleanup_repo_settings(settings)

    def test_pr_settings_creation_requires_repo_admin_permission(
            self, backend, user_util, settings_util, csrf_token):
        repo = backend.create_repo()
        repo_name = repo.repo_name

        logout_user_session(self.app, csrf_token)
        session = login_user_session(
            self.app, TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        new_csrf_token = auth.get_csrf_token(session)

        user = UserModel().get_by_username(TEST_USER_REGULAR_LOGIN)
        repo = Repository.get_by_repo_name(repo_name)
        user_util.grant_user_permission_to_repo(repo, user, 'repository.admin')
        data = self.FORM_DATA.copy()
        data['csrf_token'] = new_csrf_token
        settings = SettingsModel(repo=repo_name)

        try:
            self.app.post(
                route_path('edit_repo_vcs_update', repo_name=repo_name), data,
                status=302)
        finally:
            self._cleanup_repo_settings(settings)

    @pytest.mark.skip_backends('svn')
    def test_pr_settings_are_updated(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.repo_name
        settings = SettingsModel(repo=repo_name)
        for name in VcsSettingsModel.GENERAL_SETTINGS:
            settings.create_or_update_setting(name, True, 'bool')

        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        try:
            for name in VcsSettingsModel.GENERAL_SETTINGS:
                setting = settings.get_setting_by_name(name)
                assert setting.app_settings_value is False
        finally:
            self._cleanup_repo_settings(settings)

    def test_pr_settings_are_not_updated_for_svn(
            self, autologin_user, backend_svn, csrf_token):
        repo_name = backend_svn.repo_name
        settings = SettingsModel(repo=repo_name)
        for name in VcsSettingsModel.GENERAL_SETTINGS:
            settings.create_or_update_setting(name, True, 'bool')

        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        try:
            for name in VcsSettingsModel.GENERAL_SETTINGS:
                setting = settings.get_setting_by_name(name)
                assert setting.app_settings_value is True
        finally:
            self._cleanup_repo_settings(settings)

    def test_svn_settings_are_created(
            self, autologin_user, backend_svn, csrf_token, settings_util):
        repo_name = backend_svn.repo_name
        data = self.FORM_DATA.copy()
        data['new_svn_tag'] = 'svn-tag'
        data['new_svn_branch'] = 'svn-branch'
        data['csrf_token'] = csrf_token

        # Create few global settings to make sure that uniqueness validators
        # are not triggered
        settings_util.create_rhodecode_ui(
            VcsSettingsModel.SVN_BRANCH_SECTION, 'svn-branch')
        settings_util.create_rhodecode_ui(
            VcsSettingsModel.SVN_TAG_SECTION, 'svn-tag')

        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        settings = SettingsModel(repo=repo_name)
        try:
            svn_branches = settings.get_ui_by_section(
                VcsSettingsModel.SVN_BRANCH_SECTION)
            svn_branch_names = [b.ui_value for b in svn_branches]
            svn_tags = settings.get_ui_by_section(
                VcsSettingsModel.SVN_TAG_SECTION)
            svn_tag_names = [b.ui_value for b in svn_tags]
            assert 'svn-branch' in svn_branch_names
            assert 'svn-tag' in svn_tag_names
        finally:
            self._cleanup_repo_settings(settings)

    def test_svn_settings_are_unique(
            self, autologin_user, backend_svn, csrf_token, settings_util):
        repo = backend_svn.repo
        repo_name = repo.repo_name
        data = self.FORM_DATA.copy()
        data['new_svn_tag'] = 'test_tag'
        data['new_svn_branch'] = 'test_branch'
        data['csrf_token'] = csrf_token
        settings_util.create_repo_rhodecode_ui(
            repo, VcsSettingsModel.SVN_BRANCH_SECTION, 'test_branch')
        settings_util.create_repo_rhodecode_ui(
            repo, VcsSettingsModel.SVN_TAG_SECTION, 'test_tag')

        response = self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=200)
        response.mustcontain('Pattern already exists')

    def test_svn_settings_with_empty_values_are_not_created(
            self, autologin_user, backend_svn, csrf_token):
        repo_name = backend_svn.repo_name
        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        settings = SettingsModel(repo=repo_name)
        try:
            svn_branches = settings.get_ui_by_section(
                VcsSettingsModel.SVN_BRANCH_SECTION)
            svn_tags = settings.get_ui_by_section(
                VcsSettingsModel.SVN_TAG_SECTION)
            assert len(svn_branches) == 0
            assert len(svn_tags) == 0
        finally:
            self._cleanup_repo_settings(settings)

    def test_svn_settings_are_shown_for_svn_repository(
            self, autologin_user, backend_svn, csrf_token):
        repo_name = backend_svn.repo_name
        response = self.app.get(
            route_path('edit_repo_vcs', repo_name=repo_name), status=200)
        response.mustcontain('Subversion Settings')

    @pytest.mark.skip_backends('svn')
    def test_svn_settings_are_not_created_for_not_svn_repository(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.repo_name
        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        settings = SettingsModel(repo=repo_name)
        try:
            svn_branches = settings.get_ui_by_section(
                VcsSettingsModel.SVN_BRANCH_SECTION)
            svn_tags = settings.get_ui_by_section(
                VcsSettingsModel.SVN_TAG_SECTION)
            assert len(svn_branches) == 0
            assert len(svn_tags) == 0
        finally:
            self._cleanup_repo_settings(settings)

    @pytest.mark.skip_backends('svn')
    def test_svn_settings_are_shown_only_for_svn_repository(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.repo_name
        response = self.app.get(
            route_path('edit_repo_vcs', repo_name=repo_name), status=200)
        response.mustcontain(no='Subversion Settings')

    def test_hg_settings_are_created(
            self, autologin_user, backend_hg, csrf_token):
        repo_name = backend_hg.repo_name
        data = self.FORM_DATA.copy()
        data['new_svn_tag'] = 'svn-tag'
        data['new_svn_branch'] = 'svn-branch'
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        settings = SettingsModel(repo=repo_name)
        try:
            largefiles_ui = settings.get_ui_by_section_and_key(
                'extensions', 'largefiles')
            assert largefiles_ui.ui_active is False
            phases_ui = settings.get_ui_by_section_and_key(
                'phases', 'publish')
            assert str2bool(phases_ui.ui_value) is False
        finally:
            self._cleanup_repo_settings(settings)

    def test_hg_settings_are_updated(
            self, autologin_user, backend_hg, csrf_token):
        repo_name = backend_hg.repo_name
        settings = SettingsModel(repo=repo_name)
        settings.create_ui_section_value(
            'extensions', '', key='largefiles', active=True)
        settings.create_ui_section_value(
            'phases', '1', key='publish', active=True)

        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        try:
            largefiles_ui = settings.get_ui_by_section_and_key(
                'extensions', 'largefiles')
            assert largefiles_ui.ui_active is False
            phases_ui = settings.get_ui_by_section_and_key(
                'phases', 'publish')
            assert str2bool(phases_ui.ui_value) is False
        finally:
            self._cleanup_repo_settings(settings)

    def test_hg_settings_are_shown_for_hg_repository(
            self, autologin_user, backend_hg, csrf_token):
        repo_name = backend_hg.repo_name
        response = self.app.get(
            route_path('edit_repo_vcs', repo_name=repo_name), status=200)
        response.mustcontain('Mercurial Settings')

    @pytest.mark.skip_backends('hg')
    def test_hg_settings_are_created_only_for_hg_repository(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.repo_name
        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        settings = SettingsModel(repo=repo_name)
        try:
            largefiles_ui = settings.get_ui_by_section_and_key(
                'extensions', 'largefiles')
            assert largefiles_ui is None
            phases_ui = settings.get_ui_by_section_and_key(
                'phases', 'publish')
            assert phases_ui is None
        finally:
            self._cleanup_repo_settings(settings)

    @pytest.mark.skip_backends('hg')
    def test_hg_settings_are_shown_only_for_hg_repository(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.repo_name
        response = self.app.get(
            route_path('edit_repo_vcs', repo_name=repo_name), status=200)
        response.mustcontain(no='Mercurial Settings')

    @pytest.mark.skip_backends('hg')
    def test_hg_settings_are_updated_only_for_hg_repository(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.repo_name
        settings = SettingsModel(repo=repo_name)
        settings.create_ui_section_value(
            'extensions', '', key='largefiles', active=True)
        settings.create_ui_section_value(
            'phases', '1', key='publish', active=True)

        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)
        try:
            largefiles_ui = settings.get_ui_by_section_and_key(
                'extensions', 'largefiles')
            assert largefiles_ui.ui_active is True
            phases_ui = settings.get_ui_by_section_and_key(
                'phases', 'publish')
            assert phases_ui.ui_value == '1'
        finally:
            self._cleanup_repo_settings(settings)

    def test_per_repo_svn_settings_are_displayed(
            self, autologin_user, backend_svn, settings_util):
        repo = backend_svn.create_repo()
        repo_name = repo.repo_name
        branches = [
            settings_util.create_repo_rhodecode_ui(
                repo, VcsSettingsModel.SVN_BRANCH_SECTION,
                'branch_{}'.format(i))
            for i in range(10)]
        tags = [
            settings_util.create_repo_rhodecode_ui(
                repo, VcsSettingsModel.SVN_TAG_SECTION, 'tag_{}'.format(i))
            for i in range(10)]

        response = self.app.get(
            route_path('edit_repo_vcs', repo_name=repo_name), status=200)
        assert_response = AssertResponse(response)
        for branch in branches:
            css_selector = '[name=branch_value_{}]'.format(branch.ui_id)
            element = assert_response.get_element(css_selector)
            assert element.value == branch.ui_value
        for tag in tags:
            css_selector = '[name=tag_ui_value_new_{}]'.format(tag.ui_id)
            element = assert_response.get_element(css_selector)
            assert element.value == tag.ui_value

    def test_per_repo_hg_and_pr_settings_are_not_displayed_for_svn(
            self, autologin_user, backend_svn, settings_util):
        repo = backend_svn.create_repo()
        repo_name = repo.repo_name
        response = self.app.get(
            route_path('edit_repo_vcs', repo_name=repo_name), status=200)
        response.mustcontain(no='<label>Hooks:</label>')
        response.mustcontain(no='<label>Pull Request Settings:</label>')

    def test_inherit_global_settings_value_is_saved(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.repo_name
        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        data['inherit_global_settings'] = True
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)

        settings = SettingsModel(repo=repo_name)
        vcs_settings = VcsSettingsModel(repo=repo_name)
        try:
            assert vcs_settings.inherit_global_settings is True
        finally:
            self._cleanup_repo_settings(settings)

    def test_repo_cache_is_invalidated_when_settings_are_updated(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.repo_name
        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        data['inherit_global_settings'] = True
        settings = SettingsModel(repo=repo_name)

        invalidation_patcher = mock.patch(
            'rhodecode.model.scm.ScmModel.mark_for_invalidation')
        with invalidation_patcher as invalidation_mock:
            self.app.post(
                route_path('edit_repo_vcs_update', repo_name=repo_name), data,
                status=302)
        try:
            invalidation_mock.assert_called_once_with(repo_name, delete=True)
        finally:
            self._cleanup_repo_settings(settings)

    def test_other_settings_not_saved_inherit_global_settings_is_true(
            self, autologin_user, backend, csrf_token):
        repo_name = backend.repo_name
        data = self.FORM_DATA.copy()
        data['csrf_token'] = csrf_token
        data['inherit_global_settings'] = True
        self.app.post(
            route_path('edit_repo_vcs_update', repo_name=repo_name), data, status=302)

        settings = SettingsModel(repo=repo_name)
        ui_settings = (
            VcsSettingsModel.HOOKS_SETTINGS + VcsSettingsModel.HG_SETTINGS)

        vcs_settings = []
        try:
            for section, key in ui_settings:
                ui = settings.get_ui_by_section_and_key(section, key)
                if ui:
                    vcs_settings.append(ui)
            vcs_settings.extend(settings.get_ui_by_section(
                VcsSettingsModel.SVN_BRANCH_SECTION))
            vcs_settings.extend(settings.get_ui_by_section(
                VcsSettingsModel.SVN_TAG_SECTION))
            for name in VcsSettingsModel.GENERAL_SETTINGS:
                setting = settings.get_setting_by_name(name)
                if setting:
                    vcs_settings.append(setting)
            assert vcs_settings == []
        finally:
            self._cleanup_repo_settings(settings)

    def test_delete_svn_branch_and_tag_patterns(
            self, autologin_user, backend_svn, settings_util, csrf_token, xhr_header):
        repo = backend_svn.create_repo()
        repo_name = repo.repo_name
        branch = settings_util.create_repo_rhodecode_ui(
            repo, VcsSettingsModel.SVN_BRANCH_SECTION, 'test_branch',
            cleanup=False)
        tag = settings_util.create_repo_rhodecode_ui(
            repo, VcsSettingsModel.SVN_TAG_SECTION, 'test_tag', cleanup=False)
        data = {
            'csrf_token': csrf_token
        }
        for id_ in (branch.ui_id, tag.ui_id):
            data['delete_svn_pattern'] = id_,
            self.app.post(
                route_path('edit_repo_vcs_svn_pattern_delete', repo_name=repo_name),
                data, extra_environ=xhr_header, status=200)
        settings = VcsSettingsModel(repo=repo_name)
        assert settings.get_repo_svn_branch_patterns() == []

    def test_delete_svn_branch_requires_repo_admin_permission(
            self, backend_svn, user_util, settings_util, csrf_token, xhr_header):
        repo = backend_svn.create_repo()
        repo_name = repo.repo_name

        logout_user_session(self.app, csrf_token)
        session = login_user_session(
            self.app, TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        csrf_token = auth.get_csrf_token(session)

        repo = Repository.get_by_repo_name(repo_name)
        user = UserModel().get_by_username(TEST_USER_REGULAR_LOGIN)
        user_util.grant_user_permission_to_repo(repo, user, 'repository.admin')
        branch = settings_util.create_repo_rhodecode_ui(
            repo, VcsSettingsModel.SVN_BRANCH_SECTION, 'test_branch',
            cleanup=False)
        data = {
            'csrf_token': csrf_token,
            'delete_svn_pattern': branch.ui_id
        }
        self.app.post(
            route_path('edit_repo_vcs_svn_pattern_delete', repo_name=repo_name),
            data, extra_environ=xhr_header, status=200)

    def test_delete_svn_branch_raises_400_when_not_found(
            self, autologin_user, backend_svn, settings_util, csrf_token, xhr_header):
        repo_name = backend_svn.repo_name
        data = {
            'delete_svn_pattern': 123,
            'csrf_token': csrf_token
        }
        self.app.post(
            route_path('edit_repo_vcs_svn_pattern_delete', repo_name=repo_name),
            data, extra_environ=xhr_header, status=400)

    def test_delete_svn_branch_raises_400_when_no_id_specified(
            self, autologin_user, backend_svn, settings_util, csrf_token, xhr_header):
        repo_name = backend_svn.repo_name
        data = {
            'csrf_token': csrf_token
        }
        self.app.post(
            route_path('edit_repo_vcs_svn_pattern_delete', repo_name=repo_name),
            data, extra_environ=xhr_header, status=400)

    def _cleanup_repo_settings(self, settings_model):
        cleanup = []
        ui_settings = (
            VcsSettingsModel.HOOKS_SETTINGS + VcsSettingsModel.HG_SETTINGS)

        for section, key in ui_settings:
            ui = settings_model.get_ui_by_section_and_key(section, key)
            if ui:
                cleanup.append(ui)

        cleanup.extend(settings_model.get_ui_by_section(
            VcsSettingsModel.INHERIT_SETTINGS))
        cleanup.extend(settings_model.get_ui_by_section(
            VcsSettingsModel.SVN_BRANCH_SECTION))
        cleanup.extend(settings_model.get_ui_by_section(
            VcsSettingsModel.SVN_TAG_SECTION))

        for name in VcsSettingsModel.GENERAL_SETTINGS:
            setting = settings_model.get_setting_by_name(name)
            if setting:
                cleanup.append(setting)

        for object_ in cleanup:
            Session().delete(object_)
        Session().commit()

    def assert_repo_value_equals_global_value(self, response, setting):
        assert_response = AssertResponse(response)
        global_css_selector = '[name={}_inherited]'.format(setting)
        repo_css_selector = '[name={}]'.format(setting)
        repo_element = assert_response.get_element(repo_css_selector)
        global_element = assert_response.get_element(global_css_selector)
        assert repo_element.value == global_element.value


def _get_permission_for_user(user, repo):
    perm = UserRepoToPerm.query()\
        .filter(UserRepoToPerm.repository ==
                Repository.get_by_repo_name(repo))\
        .filter(UserRepoToPerm.user == User.get_by_username(user))\
        .all()
    return perm
