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

from rhodecode.tests import no_newline_id_generator
from rhodecode.config.middleware import (
    _sanitize_vcs_settings, _bool_setting, _string_setting, _list_setting,
    _int_setting)


class TestHelperFunctions(object):
    @pytest.mark.parametrize('raw, expected', [
        ('true', True), (u'true', True),
        ('yes', True), (u'yes', True),
        ('on', True), (u'on', True),
        ('false', False), (u'false', False),
        ('no', False), (u'no', False),
        ('off', False), (u'off', False),
        ('invalid-bool-value', False),
        ('invalid-∫øø@-√å@¨€', False),
        (u'invalid-∫øø@-√å@¨€', False),
    ])
    def test_bool_setting_helper(self, raw, expected):
        key = 'dummy-key'
        settings = {key: raw}
        _bool_setting(settings, key, None)
        assert settings[key] is expected

    @pytest.mark.parametrize('raw, expected', [
        ('', ''),
        ('test-string', 'test-string'),
        ('CaSe-TeSt', 'case-test'),
        ('test-string-çƒ©€', 'test-string-çƒ©€'),
        (u'test-string-çƒ©€', u'test-string-çƒ©€'),
    ])
    def test_string_setting_helper(self, raw, expected):
        key = 'dummy-key'
        settings = {key: raw}
        _string_setting(settings, key, None)
        assert settings[key] == expected

    @pytest.mark.parametrize('raw, expected', [
        ('', []),
        ('test', ['test']),
        ('CaSe-TeSt', ['CaSe-TeSt']),
        ('test-string-çƒ©€', ['test-string-çƒ©€']),
        (u'test-string-çƒ©€', [u'test-string-çƒ©€']),
        ('hg git svn', ['hg', 'git', 'svn']),
        ('hg,git,svn', ['hg', 'git', 'svn']),
        ('hg, git, svn', ['hg', 'git', 'svn']),
        ('hg\ngit\nsvn', ['hg', 'git', 'svn']),
        (' hg\n git\n svn ', ['hg', 'git', 'svn']),
        (', hg , git , svn , ', ['', 'hg', 'git', 'svn', '']),
        ('cheese,free node,other', ['cheese', 'free node', 'other']),
    ], ids=no_newline_id_generator)
    def test_list_setting_helper(self, raw, expected):
        key = 'dummy-key'
        settings = {key: raw}
        _list_setting(settings, key, None)
        assert settings[key] == expected

    @pytest.mark.parametrize('raw, expected', [
        ('0', 0),
        ('-0', 0),
        ('12345', 12345),
        ('-12345', -12345),
        (u'-12345', -12345),
    ])
    def test_int_setting_helper(self, raw, expected):
        key = 'dummy-key'
        settings = {key: raw}
        _int_setting(settings, key, None)
        assert settings[key] == expected

    @pytest.mark.parametrize('raw', [
        ('0xff'),
        (''),
        ('invalid-int'),
        ('invalid-⁄~†'),
        (u'invalid-⁄~†'),
    ])
    def test_int_setting_helper_invalid_input(self, raw):
        key = 'dummy-key'
        settings = {key: raw}
        with pytest.raises(Exception):
            _int_setting(settings, key, None)


class TestSanitizeVcsSettings(object):
    _bool_settings = [
        ('vcs.hooks.direct_calls', False),
        ('vcs.server.enable', True),
        ('vcs.start_server', False),
        ('startup.import_repos', False),
    ]

    _string_settings = [
        ('vcs.svn.compatible_version', ''),
        ('vcs.hooks.protocol', 'http'),
        ('vcs.hooks.host', '127.0.0.1'),
        ('vcs.scm_app_implementation', 'http'),
        ('vcs.server', ''),
        ('vcs.server.log_level', 'debug'),
        ('vcs.server.protocol', 'http'),
    ]

    _list_settings = [
        ('vcs.backends', 'hg git'),
    ]

    @pytest.mark.parametrize('key, default', _list_settings)
    def test_list_setting_spacesep_list(self, key, default):
        test_list = ['test', 'list', 'values', 'for', key]
        input_value = ' '.join(test_list)
        settings = {key: input_value}
        _sanitize_vcs_settings(settings)
        assert settings[key] == test_list

    @pytest.mark.parametrize('key, default', _list_settings)
    def test_list_setting_newlinesep_list(self, key, default):
        test_list = ['test', 'list', 'values', 'for', key]
        input_value = '\n'.join(test_list)
        settings = {key: input_value}
        _sanitize_vcs_settings(settings)
        assert settings[key] == test_list

    @pytest.mark.parametrize('key, default', _list_settings)
    def test_list_setting_commasep_list(self, key, default):
        test_list = ['test', 'list', 'values', 'for', key]
        input_value = ','.join(test_list)
        settings = {key: input_value}
        _sanitize_vcs_settings(settings)
        assert settings[key] == test_list

    @pytest.mark.parametrize('key, default', _list_settings)
    def test_list_setting_comma_and_space_sep_list(self, key, default):
        test_list = ['test', 'list', 'values', 'for', key]
        input_value = ', '.join(test_list)
        settings = {key: input_value}
        _sanitize_vcs_settings(settings)
        assert settings[key] == test_list

    @pytest.mark.parametrize('key, default', _string_settings)
    def test_string_setting_string(self, key, default):
        test_value = 'test-string-for-{}'.format(key)
        settings = {key: test_value}
        _sanitize_vcs_settings(settings)
        assert settings[key] == test_value

    @pytest.mark.parametrize('key, default', _string_settings)
    def test_string_setting_default(self, key, default):
        settings = {}
        _sanitize_vcs_settings(settings)
        assert settings[key] == default

    @pytest.mark.parametrize('key, default', _string_settings)
    def test_string_setting_lowercase(self, key, default):
        test_value = 'Test-String-For-{}'.format(key)
        settings = {key: test_value}
        _sanitize_vcs_settings(settings)
        assert settings[key] == test_value.lower()

    @pytest.mark.parametrize('key, default', _bool_settings)
    def test_bool_setting_true(self, key, default):
        settings = {key: 'true'}
        _sanitize_vcs_settings(settings)
        assert settings[key] is True

    @pytest.mark.parametrize('key, default', _bool_settings)
    def test_bool_setting_false(self, key, default):
        settings = {key: 'false'}
        _sanitize_vcs_settings(settings)
        assert settings[key] is False

    @pytest.mark.parametrize('key, default', _bool_settings)
    def test_bool_setting_invalid_string(self, key, default):
        settings = {key: 'no-bool-val-string'}
        _sanitize_vcs_settings(settings)
        assert settings[key] is False

    @pytest.mark.parametrize('key, default', _bool_settings)
    def test_bool_setting_default(self, key, default):
        settings = {}
        _sanitize_vcs_settings(settings)
        assert settings[key] is default
