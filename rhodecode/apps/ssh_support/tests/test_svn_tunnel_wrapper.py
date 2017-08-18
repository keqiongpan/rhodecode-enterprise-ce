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


import subprocess
from io import BytesIO
from time import sleep

import pytest
from mock import patch, Mock, MagicMock, call

from rhodecode.apps.ssh_support.lib.ssh_wrapper import SubversionTunnelWrapper
from rhodecode.tests import no_newline_id_generator


class TestSubversionTunnelWrapper(object):
    @pytest.mark.parametrize(
        'input_string, output_string', [
            [None, ''],
            ['abcde', '5:abcde '],
            ['abcdefghijk', '11:abcdefghijk ']
        ])
    def test_svn_string(self, input_string, output_string):
        wrapper = SubversionTunnelWrapper(timeout=5)
        assert wrapper._svn_string(input_string) == output_string

    def test_read_first_client_response(self):
        wrapper = SubversionTunnelWrapper(timeout=5)
        buffer_ = '( abcd ( efg hij ) ) '
        wrapper.stdin = BytesIO(buffer_)
        result = wrapper._read_first_client_response()
        assert result == buffer_

    def test_parse_first_client_response_returns_dict(self):
        response = (
            '( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo'
            ' log-revprops ) 26:svn+ssh://vcs@vm/hello-svn 38:SVN/1.8.11'
            ' (x86_64-apple-darwin14.1.0) ( ) ) ')
        wrapper = SubversionTunnelWrapper(timeout=5)
        result = wrapper._parse_first_client_response(response)
        assert result['version'] == '2'
        assert (
            result['capabilities'] ==
            'edit-pipeline svndiff1 absent-entries depth mergeinfo'
            ' log-revprops')
        assert result['url'] == 'svn+ssh://vcs@vm/hello-svn'
        assert result['ra_client'] == 'SVN/1.8.11 (x86_64-apple-darwin14.1.0)'
        assert result['client'] is None

    def test_parse_first_client_response_returns_none_when_not_matched(self):
        response = (
            '( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo'
            ' log-revprops ) ) ')
        wrapper = SubversionTunnelWrapper(timeout=5)
        result = wrapper._parse_first_client_response(response)
        assert result is None

    def test_interrupt(self):
        wrapper = SubversionTunnelWrapper(timeout=5)
        with patch.object(wrapper, 'fail') as fail_mock:
            wrapper.interrupt(1, 'frame')
            fail_mock.assert_called_once_with("Exited by timeout")

    def test_fail(self):
        process_mock = Mock()
        wrapper = SubversionTunnelWrapper(timeout=5)
        with patch.object(wrapper, 'remove_configs') as remove_configs_mock:
            with patch('sys.stdout', new_callable=BytesIO) as stdout_mock:
                with patch.object(wrapper, 'process') as process_mock:
                    wrapper.fail('test message')
        assert (
            stdout_mock.getvalue() ==
            '( failure ( ( 210005 12:test message  0: 0 ) ) )\n')
        process_mock.kill.assert_called_once_with()
        remove_configs_mock.assert_called_once_with()

    @pytest.mark.parametrize(
        'client, expected_client', [
            ['test ', 'test '],
            ['', ''],
            [None, '']
        ])
    def test_client_in_patch_first_client_response(
            self, client, expected_client):
        response = {
            'version': 2,
            'capabilities': 'edit-pipeline svndiff1 absent-entries depth',
            'url': 'svn+ssh://example.com/svn',
            'ra_client': 'SVN/1.8.11 (x86_64-apple-darwin14.1.0)',
            'client': client
        }
        wrapper = SubversionTunnelWrapper(timeout=5)
        stdin = BytesIO()
        with patch.object(wrapper, 'process') as process_mock:
            process_mock.stdin = stdin
            wrapper.patch_first_client_response(response)
        assert (
            stdin.getvalue() ==
            '( 2 ( edit-pipeline svndiff1 absent-entries depth )'
            ' 25:svn+ssh://example.com/svn 38:SVN/1.8.11'
            ' (x86_64-apple-darwin14.1.0) ( {expected_client}) ) '.format(
                expected_client=expected_client))

    def test_kwargs_override_data_in_patch_first_client_response(self):
        response = {
            'version': 2,
            'capabilities': 'edit-pipeline svndiff1 absent-entries depth',
            'url': 'svn+ssh://example.com/svn',
            'ra_client': 'SVN/1.8.11 (x86_64-apple-darwin14.1.0)',
            'client': 'test'
        }
        wrapper = SubversionTunnelWrapper(timeout=5)
        stdin = BytesIO()
        with patch.object(wrapper, 'process') as process_mock:
            process_mock.stdin = stdin
            wrapper.patch_first_client_response(
                response, version=3, client='abcde ',
                capabilities='absent-entries depth',
                url='svn+ssh://example.org/test',
                ra_client='SVN/1.8.12 (ubuntu 14.04)')
        assert (
            stdin.getvalue() ==
            '( 3 ( absent-entries depth ) 26:svn+ssh://example.org/test'
            ' 25:SVN/1.8.12 (ubuntu 14.04) ( abcde ) ) ')

    def test_patch_first_client_response_sets_environment(self):
        response = {
            'version': 2,
            'capabilities': 'edit-pipeline svndiff1 absent-entries depth',
            'url': 'svn+ssh://example.com/svn',
            'ra_client': 'SVN/1.8.11 (x86_64-apple-darwin14.1.0)',
            'client': 'test'
        }
        wrapper = SubversionTunnelWrapper(timeout=5)
        stdin = BytesIO()
        with patch.object(wrapper, 'create_hooks_env') as create_hooks_mock:
            with patch.object(wrapper, 'process') as process_mock:
                process_mock.stdin = stdin
                wrapper.patch_first_client_response(response)
        create_hooks_mock.assert_called_once_with()

    def test_get_first_client_response_exits_by_signal(self):
        wrapper = SubversionTunnelWrapper(timeout=1)
        read_patch = patch.object(wrapper, '_read_first_client_response')
        parse_patch = patch.object(wrapper, '_parse_first_client_response')
        interrupt_patch = patch.object(wrapper, 'interrupt')

        with read_patch as read_mock, parse_patch as parse_mock, \
                interrupt_patch as interrupt_mock:
            read_mock.side_effect = lambda: sleep(3)
            wrapper.get_first_client_response()

        assert parse_mock.call_count == 0
        assert interrupt_mock.call_count == 1

    def test_get_first_client_response_parses_data(self):
        wrapper = SubversionTunnelWrapper(timeout=5)
        response = (
            '( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo'
            ' log-revprops ) 26:svn+ssh://vcs@vm/hello-svn 38:SVN/1.8.11'
            ' (x86_64-apple-darwin14.1.0) ( ) ) ')
        read_patch = patch.object(wrapper, '_read_first_client_response')
        parse_patch = patch.object(wrapper, '_parse_first_client_response')

        with read_patch as read_mock, parse_patch as parse_mock:
            read_mock.return_value = response
            wrapper.get_first_client_response()

        parse_mock.assert_called_once_with(response)

    def test_return_code(self):
        wrapper = SubversionTunnelWrapper(timeout=5)
        with patch.object(wrapper, 'process') as process_mock:
            process_mock.returncode = 1
            assert wrapper.return_code == 1

    def test_sync_loop_breaks_when_process_cannot_be_polled(self):
        self.counter = 0
        buffer_ = 'abcdefghij'

        wrapper = SubversionTunnelWrapper(timeout=5)
        wrapper.stdin = BytesIO(buffer_)
        with patch.object(wrapper, 'remove_configs') as remove_configs_mock:
            with patch.object(wrapper, 'process') as process_mock:
                process_mock.poll.side_effect = self._poll
                process_mock.stdin = BytesIO()
                wrapper.sync()
        assert process_mock.stdin.getvalue() == 'abcde'
        remove_configs_mock.assert_called_once_with()

    def test_sync_loop_breaks_when_nothing_to_read(self):
        self.counter = 0
        buffer_ = 'abcdefghij'

        wrapper = SubversionTunnelWrapper(timeout=5)
        wrapper.stdin = BytesIO(buffer_)
        with patch.object(wrapper, 'remove_configs') as remove_configs_mock:
            with patch.object(wrapper, 'process') as process_mock:
                process_mock.poll.return_value = None
                process_mock.stdin = BytesIO()
                wrapper.sync()
        assert process_mock.stdin.getvalue() == buffer_
        remove_configs_mock.assert_called_once_with()

    def test_start_without_repositories_root(self):
        svn_path = '/usr/local/bin/svnserve'
        wrapper = SubversionTunnelWrapper(timeout=5, svn_path=svn_path)
        with patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.Popen') as popen_mock:
            wrapper.start()
        expected_command = [
            svn_path, '-t', '--config-file', wrapper.svn_conf_path]
        popen_mock.assert_called_once_with(
            expected_command, stdin=subprocess.PIPE)
        assert wrapper.process == popen_mock()

    def test_start_with_repositories_root(self):
        svn_path = '/usr/local/bin/svnserve'
        repositories_root = '/home/repos'
        wrapper = SubversionTunnelWrapper(
            timeout=5, svn_path=svn_path, repositories_root=repositories_root)
        with patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.Popen') as popen_mock:
            wrapper.start()
        expected_command = [
            svn_path, '-t', '--config-file', wrapper.svn_conf_path,
            '-r', repositories_root]
        popen_mock.assert_called_once_with(
            expected_command, stdin=subprocess.PIPE)
        assert wrapper.process == popen_mock()

    def test_create_svn_config(self):
        wrapper = SubversionTunnelWrapper(timeout=5)
        file_mock = MagicMock(spec=file)
        with patch('os.fdopen', create=True) as open_mock:
            open_mock.return_value = file_mock
            wrapper.create_svn_config()
        open_mock.assert_called_once_with(wrapper.svn_conf_fd, 'w')
        expected_content = '[general]\nhooks-env = {}\n'.format(
            wrapper.hooks_env_path)
        file_handle = file_mock.__enter__.return_value
        file_handle.write.assert_called_once_with(expected_content)

    @pytest.mark.parametrize(
        'read_only, expected_content', [
            [True, '[default]\nLANG = en_US.UTF-8\nSSH_READ_ONLY = 1\n'],
            [False, '[default]\nLANG = en_US.UTF-8\n']
        ], ids=no_newline_id_generator)
    def test_create_hooks_env(self, read_only, expected_content):
        wrapper = SubversionTunnelWrapper(timeout=5)
        wrapper.read_only = read_only
        file_mock = MagicMock(spec=file)
        with patch('os.fdopen', create=True) as open_mock:
            open_mock.return_value = file_mock
            wrapper.create_hooks_env()
        open_mock.assert_called_once_with(wrapper.hooks_env_fd, 'w')
        file_handle = file_mock.__enter__.return_value
        file_handle.write.assert_called_once_with(expected_content)

    def test_remove_configs(self):
        wrapper = SubversionTunnelWrapper(timeout=5)
        with patch('os.remove') as remove_mock:
            wrapper.remove_configs()
        expected_calls = [
            call(wrapper.svn_conf_path), call(wrapper.hooks_env_path)]
        assert sorted(remove_mock.call_args_list) == sorted(expected_calls)

    def _poll(self):
        self.counter += 1
        return None if self.counter < 6 else 1
