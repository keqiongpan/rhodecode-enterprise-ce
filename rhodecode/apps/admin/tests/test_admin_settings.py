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

import mock
import pytest

import rhodecode
from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.lib.utils2 import md5
from rhodecode.model.db import RhodeCodeUi
from rhodecode.model.meta import Session
from rhodecode.model.settings import SettingsModel, IssueTrackerSettingsModel
from rhodecode.tests import assert_session_flash
from rhodecode.tests.utils import AssertResponse


UPDATE_DATA_QUALNAME = 'rhodecode.model.update.UpdateModel.get_update_data'


def route_path(name, params=None, **kwargs):
    import urllib
    from rhodecode.apps._base import ADMIN_PREFIX

    base_url = {

        'admin_settings':
            ADMIN_PREFIX +'/settings',
        'admin_settings_update':
            ADMIN_PREFIX + '/settings/update',
        'admin_settings_global':
            ADMIN_PREFIX + '/settings/global',
        'admin_settings_global_update':
            ADMIN_PREFIX + '/settings/global/update',
        'admin_settings_vcs':
            ADMIN_PREFIX + '/settings/vcs',
        'admin_settings_vcs_update':
            ADMIN_PREFIX + '/settings/vcs/update',
        'admin_settings_vcs_svn_pattern_delete':
            ADMIN_PREFIX + '/settings/vcs/svn_pattern_delete',
        'admin_settings_mapping':
            ADMIN_PREFIX + '/settings/mapping',
        'admin_settings_mapping_update':
            ADMIN_PREFIX + '/settings/mapping/update',
        'admin_settings_visual':
            ADMIN_PREFIX + '/settings/visual',
        'admin_settings_visual_update':
            ADMIN_PREFIX + '/settings/visual/update',
        'admin_settings_issuetracker':
            ADMIN_PREFIX + '/settings/issue-tracker',
        'admin_settings_issuetracker_update':
            ADMIN_PREFIX + '/settings/issue-tracker/update',
        'admin_settings_issuetracker_test':
            ADMIN_PREFIX + '/settings/issue-tracker/test',
        'admin_settings_issuetracker_delete':
            ADMIN_PREFIX + '/settings/issue-tracker/delete',
        'admin_settings_email':
            ADMIN_PREFIX + '/settings/email',
        'admin_settings_email_update':
            ADMIN_PREFIX + '/settings/email/update',
        'admin_settings_hooks':
            ADMIN_PREFIX + '/settings/hooks',
        'admin_settings_hooks_update':
            ADMIN_PREFIX + '/settings/hooks/update',
        'admin_settings_hooks_delete':
            ADMIN_PREFIX + '/settings/hooks/delete',
        'admin_settings_search':
            ADMIN_PREFIX + '/settings/search',
        'admin_settings_labs':
            ADMIN_PREFIX + '/settings/labs',
        'admin_settings_labs_update':
            ADMIN_PREFIX + '/settings/labs/update',

        'admin_settings_sessions':
            ADMIN_PREFIX + '/settings/sessions',
        'admin_settings_sessions_cleanup':
            ADMIN_PREFIX + '/settings/sessions/cleanup',
        'admin_settings_system':
            ADMIN_PREFIX + '/settings/system',
        'admin_settings_system_update':
            ADMIN_PREFIX + '/settings/system/updates',
        'admin_settings_open_source':
            ADMIN_PREFIX + '/settings/open_source',


    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.usefixtures('autologin_user', 'app')
class TestAdminSettingsController(object):

    @pytest.mark.parametrize('urlname', [
        'admin_settings_vcs',
        'admin_settings_mapping',
        'admin_settings_global',
        'admin_settings_visual',
        'admin_settings_email',
        'admin_settings_hooks',
        'admin_settings_search',
    ])
    def test_simple_get(self, urlname):
        self.app.get(route_path(urlname))

    def test_create_custom_hook(self, csrf_token):
        response = self.app.post(
            route_path('admin_settings_hooks_update'),
            params={
                'new_hook_ui_key': 'test_hooks_1',
                'new_hook_ui_value': 'cd /tmp',
                'csrf_token': csrf_token})

        response = response.follow()
        response.mustcontain('test_hooks_1')
        response.mustcontain('cd /tmp')

    def test_create_custom_hook_delete(self, csrf_token):
        response = self.app.post(
            route_path('admin_settings_hooks_update'),
            params={
                'new_hook_ui_key': 'test_hooks_2',
                'new_hook_ui_value': 'cd /tmp2',
                'csrf_token': csrf_token})

        response = response.follow()
        response.mustcontain('test_hooks_2')
        response.mustcontain('cd /tmp2')

        hook_id = SettingsModel().get_ui_by_key('test_hooks_2').ui_id

        # delete
        self.app.post(
            route_path('admin_settings_hooks_delete'),
            params={'hook_id': hook_id, 'csrf_token': csrf_token})
        response = self.app.get(route_path('admin_settings_hooks'))
        response.mustcontain(no=['test_hooks_2'])
        response.mustcontain(no=['cd /tmp2'])


@pytest.mark.usefixtures('autologin_user', 'app')
class TestAdminSettingsGlobal(object):

    def test_pre_post_code_code_active(self, csrf_token):
        pre_code = 'rc-pre-code-187652122'
        post_code = 'rc-postcode-98165231'

        response = self.post_and_verify_settings({
            'rhodecode_pre_code': pre_code,
            'rhodecode_post_code': post_code,
            'csrf_token': csrf_token,
        })

        response = response.follow()
        response.mustcontain(pre_code, post_code)

    def test_pre_post_code_code_inactive(self, csrf_token):
        pre_code = 'rc-pre-code-187652122'
        post_code = 'rc-postcode-98165231'
        response = self.post_and_verify_settings({
            'rhodecode_pre_code': '',
            'rhodecode_post_code': '',
            'csrf_token': csrf_token,
        })

        response = response.follow()
        response.mustcontain(no=[pre_code, post_code])

    def test_captcha_activate(self, csrf_token):
        self.post_and_verify_settings({
            'rhodecode_captcha_private_key': '1234567890',
            'rhodecode_captcha_public_key': '1234567890',
            'csrf_token': csrf_token,
        })

        response = self.app.get(ADMIN_PREFIX + '/register')
        response.mustcontain('captcha')

    def test_captcha_deactivate(self, csrf_token):
        self.post_and_verify_settings({
            'rhodecode_captcha_private_key': '',
            'rhodecode_captcha_public_key': '1234567890',
            'csrf_token': csrf_token,
        })

        response = self.app.get(ADMIN_PREFIX + '/register')
        response.mustcontain(no=['captcha'])

    def test_title_change(self, csrf_token):
        old_title = 'RhodeCode'

        for new_title in ['Changed', 'Żółwik', old_title]:
            response = self.post_and_verify_settings({
                'rhodecode_title': new_title,
                'csrf_token': csrf_token,
            })

            response = response.follow()
            response.mustcontain(
                """<div class="branding">- %s</div>""" % new_title)

    def post_and_verify_settings(self, settings):
        old_title = 'RhodeCode'
        old_realm = 'RhodeCode authentication'
        params = {
            'rhodecode_title': old_title,
            'rhodecode_realm': old_realm,
            'rhodecode_pre_code': '',
            'rhodecode_post_code': '',
            'rhodecode_captcha_private_key': '',
            'rhodecode_captcha_public_key': '',
            'rhodecode_create_personal_repo_group': False,
            'rhodecode_personal_repo_group_pattern': '${username}',
        }
        params.update(settings)
        response = self.app.post(
            route_path('admin_settings_global_update'), params=params)

        assert_session_flash(response, 'Updated application settings')
        app_settings = SettingsModel().get_all_settings()
        del settings['csrf_token']
        for key, value in settings.iteritems():
            assert app_settings[key] == value.decode('utf-8')

        return response


@pytest.mark.usefixtures('autologin_user', 'app')
class TestAdminSettingsVcs(object):

    def test_contains_svn_default_patterns(self):
        response = self.app.get(route_path('admin_settings_vcs'))
        expected_patterns = [
            '/trunk',
            '/branches/*',
            '/tags/*',
        ]
        for pattern in expected_patterns:
            response.mustcontain(pattern)

    def test_add_new_svn_branch_and_tag_pattern(
            self, backend_svn, form_defaults, disable_sql_cache,
            csrf_token):
        form_defaults.update({
            'new_svn_branch': '/exp/branches/*',
            'new_svn_tag': '/important_tags/*',
            'csrf_token': csrf_token,
        })

        response = self.app.post(
            route_path('admin_settings_vcs_update'),
            params=form_defaults, status=302)
        response = response.follow()

        # Expect to find the new values on the page
        response.mustcontain('/exp/branches/*')
        response.mustcontain('/important_tags/*')

        # Expect that those patterns are used to match branches and tags now
        repo = backend_svn['svn-simple-layout'].scm_instance()
        assert 'exp/branches/exp-sphinx-docs' in repo.branches
        assert 'important_tags/v0.5' in repo.tags

    def test_add_same_svn_value_twice_shows_an_error_message(
            self, form_defaults, csrf_token, settings_util):
        settings_util.create_rhodecode_ui('vcs_svn_branch', '/test')
        settings_util.create_rhodecode_ui('vcs_svn_tag', '/test')

        response = self.app.post(
            route_path('admin_settings_vcs_update'),
            params={
                'paths_root_path': form_defaults['paths_root_path'],
                'new_svn_branch': '/test',
                'new_svn_tag': '/test',
                'csrf_token': csrf_token,
            },
            status=200)

        response.mustcontain("Pattern already exists")
        response.mustcontain("Some form inputs contain invalid data.")

    @pytest.mark.parametrize('section', [
        'vcs_svn_branch',
        'vcs_svn_tag',
    ])
    def test_delete_svn_patterns(
            self, section, csrf_token, settings_util):
        setting = settings_util.create_rhodecode_ui(
            section, '/test_delete', cleanup=False)

        self.app.post(
            route_path('admin_settings_vcs_svn_pattern_delete'),
            params={
                'delete_svn_pattern': setting.ui_id,
                'csrf_token': csrf_token},
            headers={'X-REQUESTED-WITH': 'XMLHttpRequest'})

    @pytest.mark.parametrize('section', [
        'vcs_svn_branch',
        'vcs_svn_tag',
    ])
    def test_delete_svn_patterns_raises_404_when_no_xhr(
            self, section, csrf_token, settings_util):
        setting = settings_util.create_rhodecode_ui(section, '/test_delete')

        self.app.post(
            route_path('admin_settings_vcs_svn_pattern_delete'),
            params={
                'delete_svn_pattern': setting.ui_id,
                'csrf_token': csrf_token},
            status=404)

    def test_extensions_hgsubversion(self, form_defaults, csrf_token):
        form_defaults.update({
            'csrf_token': csrf_token,
            'extensions_hgsubversion': 'True',
        })
        response = self.app.post(
            route_path('admin_settings_vcs_update'),
            params=form_defaults,
            status=302)

        response = response.follow()
        extensions_input = (
            '<input id="extensions_hgsubversion" '
            'name="extensions_hgsubversion" type="checkbox" '
            'value="True" checked="checked" />')
        response.mustcontain(extensions_input)

    def test_extensions_hgevolve(self, form_defaults, csrf_token):
        form_defaults.update({
            'csrf_token': csrf_token,
            'extensions_evolve': 'True',
        })
        response = self.app.post(
            route_path('admin_settings_vcs_update'),
            params=form_defaults,
            status=302)

        response = response.follow()
        extensions_input = (
            '<input id="extensions_evolve" '
            'name="extensions_evolve" type="checkbox" '
            'value="True" checked="checked" />')
        response.mustcontain(extensions_input)

    def test_has_a_section_for_pull_request_settings(self):
        response = self.app.get(route_path('admin_settings_vcs'))
        response.mustcontain('Pull Request Settings')

    def test_has_an_input_for_invalidation_of_inline_comments(self):
        response = self.app.get(route_path('admin_settings_vcs'))
        assert_response = AssertResponse(response)
        assert_response.one_element_exists(
            '[name=rhodecode_use_outdated_comments]')

    @pytest.mark.parametrize('new_value', [True, False])
    def test_allows_to_change_invalidation_of_inline_comments(
            self, form_defaults, csrf_token, new_value):
        setting_key = 'use_outdated_comments'
        setting = SettingsModel().create_or_update_setting(
            setting_key, not new_value, 'bool')
        Session().add(setting)
        Session().commit()

        form_defaults.update({
            'csrf_token': csrf_token,
            'rhodecode_use_outdated_comments': str(new_value),
        })
        response = self.app.post(
            route_path('admin_settings_vcs_update'),
            params=form_defaults,
            status=302)
        response = response.follow()
        setting = SettingsModel().get_setting_by_name(setting_key)
        assert setting.app_settings_value is new_value

    @pytest.mark.parametrize('new_value', [True, False])
    def test_allows_to_change_hg_rebase_merge_strategy(
            self, form_defaults, csrf_token, new_value):
        setting_key = 'hg_use_rebase_for_merging'

        form_defaults.update({
            'csrf_token': csrf_token,
            'rhodecode_' + setting_key: str(new_value),
        })

        with mock.patch.dict(
                rhodecode.CONFIG, {'labs_settings_active': 'true'}):
            self.app.post(
                route_path('admin_settings_vcs_update'),
                params=form_defaults,
                status=302)

        setting = SettingsModel().get_setting_by_name(setting_key)
        assert setting.app_settings_value is new_value

    @pytest.fixture
    def disable_sql_cache(self, request):
        patcher = mock.patch(
            'rhodecode.lib.caching_query.FromCache.process_query')
        request.addfinalizer(patcher.stop)
        patcher.start()

    @pytest.fixture
    def form_defaults(self):
        from rhodecode.apps.admin.views.settings import AdminSettingsView
        return AdminSettingsView._form_defaults()

    # TODO: johbo: What we really want is to checkpoint before a test run and
    # reset the session afterwards.
    @pytest.fixture(scope='class', autouse=True)
    def cleanup_settings(self, request, baseapp):
        ui_id = RhodeCodeUi.ui_id
        original_ids = list(
            r.ui_id for r in RhodeCodeUi.query().values(ui_id))

        @request.addfinalizer
        def cleanup():
            RhodeCodeUi.query().filter(
                ui_id.notin_(original_ids)).delete(False)


@pytest.mark.usefixtures('autologin_user', 'app')
class TestLabsSettings(object):
    def test_get_settings_page_disabled(self):
        with mock.patch.dict(
                rhodecode.CONFIG, {'labs_settings_active': 'false'}):

            response = self.app.get(
                route_path('admin_settings_labs'), status=302)

        assert response.location.endswith(route_path('admin_settings'))

    def test_get_settings_page_enabled(self):
        from rhodecode.apps.admin.views import settings
        lab_settings = [
            settings.LabSetting(
                key='rhodecode_bool',
                type='bool',
                group='bool group',
                label='bool label',
                help='bool help'
            ),
            settings.LabSetting(
                key='rhodecode_text',
                type='unicode',
                group='text group',
                label='text label',
                help='text help'
            ),
        ]
        with mock.patch.dict(rhodecode.CONFIG,
                             {'labs_settings_active': 'true'}):
            with mock.patch.object(settings, '_LAB_SETTINGS', lab_settings):
                response = self.app.get(route_path('admin_settings_labs'))

        assert '<label>bool group:</label>' in response
        assert '<label for="rhodecode_bool">bool label</label>' in response
        assert '<p class="help-block">bool help</p>' in response
        assert 'name="rhodecode_bool" type="checkbox"' in response

        assert '<label>text group:</label>' in response
        assert '<label for="rhodecode_text">text label</label>' in response
        assert '<p class="help-block">text help</p>' in response
        assert 'name="rhodecode_text" size="60" type="text"' in response


@pytest.mark.usefixtures('app')
class TestOpenSourceLicenses(object):

    def test_records_are_displayed(self, autologin_user):
        sample_licenses = {
            "python2.7-pytest-2.7.1": {
                "UNKNOWN": None
            },
            "python2.7-Markdown-2.6.2": {
                "BSD-3-Clause": "http://spdx.org/licenses/BSD-3-Clause"
            }
        }
        read_licenses_patch = mock.patch(
            'rhodecode.apps.admin.views.open_source_licenses.read_opensource_licenses',
            return_value=sample_licenses)
        with read_licenses_patch:
            response = self.app.get(
                route_path('admin_settings_open_source'), status=200)

        assert_response = AssertResponse(response)
        assert_response.element_contains(
            '.panel-heading', 'Licenses of Third Party Packages')
        for name in sample_licenses:
            response.mustcontain(name)
            for license in sample_licenses[name]:
                assert_response.element_contains('.panel-body', license)

    def test_records_can_be_read(self, autologin_user):
        response = self.app.get(
            route_path('admin_settings_open_source'), status=200)
        assert_response = AssertResponse(response)
        assert_response.element_contains(
            '.panel-heading', 'Licenses of Third Party Packages')

    def test_forbidden_when_normal_user(self, autologin_regular_user):
        self.app.get(
            route_path('admin_settings_open_source'), status=404)


@pytest.mark.usefixtures('app')
class TestUserSessions(object):

    def test_forbidden_when_normal_user(self, autologin_regular_user):
        self.app.get(route_path('admin_settings_sessions'), status=404)

    def test_show_sessions_page(self, autologin_user):
        response = self.app.get(route_path('admin_settings_sessions'), status=200)
        response.mustcontain('file')

    def test_cleanup_old_sessions(self, autologin_user, csrf_token):

        post_data = {
            'csrf_token': csrf_token,
            'expire_days': '60'
        }
        response = self.app.post(
            route_path('admin_settings_sessions_cleanup'), params=post_data,
            status=302)
        assert_session_flash(response, 'Cleaned up old sessions')


@pytest.mark.usefixtures('app')
class TestAdminSystemInfo(object):

    def test_forbidden_when_normal_user(self, autologin_regular_user):
        self.app.get(route_path('admin_settings_system'), status=404)

    def test_system_info_page(self, autologin_user):
        response = self.app.get(route_path('admin_settings_system'))
        response.mustcontain('RhodeCode Community Edition, version {}'.format(
            rhodecode.__version__))

    def test_system_update_new_version(self, autologin_user):
        update_data = {
            'versions': [
                {
                    'version': '100.3.1415926535',
                    'general': 'The latest version we are ever going to ship'
                },
                {
                    'version': '0.0.0',
                    'general': 'The first version we ever shipped'
                }
            ]
        }
        with mock.patch(UPDATE_DATA_QUALNAME, return_value=update_data):
            response = self.app.get(route_path('admin_settings_system_update'))
            response.mustcontain('A <b>new version</b> is available')

    def test_system_update_nothing_new(self, autologin_user):
        update_data = {
            'versions': [
                {
                    'version': '0.0.0',
                    'general': 'The first version we ever shipped'
                }
            ]
        }
        with mock.patch(UPDATE_DATA_QUALNAME, return_value=update_data):
            response = self.app.get(route_path('admin_settings_system_update'))
            response.mustcontain(
                'This instance is already running the <b>latest</b> stable version')

    def test_system_update_bad_response(self, autologin_user):
        with mock.patch(UPDATE_DATA_QUALNAME, side_effect=ValueError('foo')):
            response = self.app.get(route_path('admin_settings_system_update'))
            response.mustcontain(
                'Bad data sent from update server')


@pytest.mark.usefixtures("app")
class TestAdminSettingsIssueTracker(object):
    RC_PREFIX = 'rhodecode_'
    SHORT_PATTERN_KEY = 'issuetracker_pat_'
    PATTERN_KEY = RC_PREFIX + SHORT_PATTERN_KEY

    def test_issuetracker_index(self, autologin_user):
        response = self.app.get(route_path('admin_settings_issuetracker'))
        assert response.status_code == 200

    def test_add_empty_issuetracker_pattern(
            self, request, autologin_user, csrf_token):
        post_url = route_path('admin_settings_issuetracker_update')
        post_data = {
            'csrf_token': csrf_token
        }
        self.app.post(post_url, post_data, status=302)

    def test_add_issuetracker_pattern(
            self, request, autologin_user, csrf_token):
        pattern = 'issuetracker_pat'
        another_pattern = pattern+'1'
        post_url = route_path('admin_settings_issuetracker_update')
        post_data = {
            'new_pattern_pattern_0': pattern,
            'new_pattern_url_0': 'http://url',
            'new_pattern_prefix_0': 'prefix',
            'new_pattern_description_0': 'description',
            'new_pattern_pattern_1': another_pattern,
            'new_pattern_url_1': 'https://url1',
            'new_pattern_prefix_1': 'prefix1',
            'new_pattern_description_1': 'description1',
            'csrf_token': csrf_token
        }
        self.app.post(post_url, post_data, status=302)
        settings = SettingsModel().get_all_settings()
        self.uid = md5(pattern)
        assert settings[self.PATTERN_KEY+self.uid] == pattern
        self.another_uid = md5(another_pattern)
        assert settings[self.PATTERN_KEY+self.another_uid] == another_pattern

        @request.addfinalizer
        def cleanup():
            defaults = SettingsModel().get_all_settings()

            entries = [name for name in defaults if (
                (self.uid in name) or (self.another_uid) in name)]
            start = len(self.RC_PREFIX)
            for del_key in entries:
                # TODO: anderson: get_by_name needs name without prefix
                entry = SettingsModel().get_setting_by_name(del_key[start:])
                Session().delete(entry)

            Session().commit()

    def test_edit_issuetracker_pattern(
            self, autologin_user, backend, csrf_token, request):
        old_pattern = 'issuetracker_pat'
        old_uid = md5(old_pattern)
        pattern = 'issuetracker_pat_new'
        self.new_uid = md5(pattern)

        SettingsModel().create_or_update_setting(
            self.SHORT_PATTERN_KEY+old_uid, old_pattern, 'unicode')

        post_url = route_path('admin_settings_issuetracker_update')
        post_data = {
            'new_pattern_pattern_0': pattern,
            'new_pattern_url_0': 'https://url',
            'new_pattern_prefix_0': 'prefix',
            'new_pattern_description_0': 'description',
            'uid': old_uid,
            'csrf_token': csrf_token
        }
        self.app.post(post_url, post_data, status=302)
        settings = SettingsModel().get_all_settings()
        assert settings[self.PATTERN_KEY+self.new_uid] == pattern
        assert self.PATTERN_KEY+old_uid not in settings

        @request.addfinalizer
        def cleanup():
            IssueTrackerSettingsModel().delete_entries(self.new_uid)

    def test_replace_issuetracker_pattern_description(
            self, autologin_user, csrf_token, request, settings_util):
        prefix = 'issuetracker'
        pattern = 'issuetracker_pat'
        self.uid = md5(pattern)
        pattern_key = '_'.join([prefix, 'pat', self.uid])
        rc_pattern_key = '_'.join(['rhodecode', pattern_key])
        desc_key = '_'.join([prefix, 'desc', self.uid])
        rc_desc_key = '_'.join(['rhodecode', desc_key])
        new_description = 'new_description'

        settings_util.create_rhodecode_setting(
            pattern_key, pattern, 'unicode', cleanup=False)
        settings_util.create_rhodecode_setting(
            desc_key, 'old description', 'unicode', cleanup=False)

        post_url = route_path('admin_settings_issuetracker_update')
        post_data = {
            'new_pattern_pattern_0': pattern,
            'new_pattern_url_0': 'https://url',
            'new_pattern_prefix_0': 'prefix',
            'new_pattern_description_0': new_description,
            'uid': self.uid,
            'csrf_token': csrf_token
        }
        self.app.post(post_url, post_data, status=302)
        settings = SettingsModel().get_all_settings()
        assert settings[rc_pattern_key] == pattern
        assert settings[rc_desc_key] == new_description

        @request.addfinalizer
        def cleanup():
            IssueTrackerSettingsModel().delete_entries(self.uid)

    def test_delete_issuetracker_pattern(
            self, autologin_user, backend, csrf_token, settings_util):
        pattern = 'issuetracker_pat'
        uid = md5(pattern)
        settings_util.create_rhodecode_setting(
            self.SHORT_PATTERN_KEY+uid, pattern, 'unicode', cleanup=False)

        post_url = route_path('admin_settings_issuetracker_delete')
        post_data = {
            '_method': 'delete',
            'uid': uid,
            'csrf_token': csrf_token
        }
        self.app.post(post_url, post_data, status=302)
        settings = SettingsModel().get_all_settings()
        assert 'rhodecode_%s%s' % (self.SHORT_PATTERN_KEY, uid) not in settings
