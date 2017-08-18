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
import os
import mock
import pytest
import ConfigParser

from rhodecode.apps.ssh_support.lib.ssh_wrapper import SshWrapper


@pytest.fixture
def dummy_conf(tmpdir):
    conf = ConfigParser.ConfigParser()
    conf.add_section('app:main')
    conf.set('app:main', 'ssh.executable.hg', '/usr/bin/hg')
    conf.set('app:main', 'ssh.executable.git', '/usr/bin/git')
    conf.set('app:main', 'ssh.executable.svn', '/usr/bin/svnserve')

    conf.set('app:main', 'ssh.api_key', 'xxx')
    conf.set('app:main', 'ssh.api_host', 'http://localhost')

    f_path = os.path.join(str(tmpdir), 'ssh_wrapper_test.ini')
    with open(f_path, 'wb') as f:
        conf.write(f)

    return os.path.join(f_path)


class TestGetRepoDetails(object):
    @pytest.mark.parametrize(
        'command', [
            'hg -R test-repo serve --stdio',
            'hg     -R      test-repo      serve       --stdio'
        ])
    def test_hg_command_matched(self, command, dummy_conf):
        wrapper = SshWrapper(command, 'auto', 'admin', '3', 'False', dummy_conf)
        type_, name, mode = wrapper.get_repo_details('auto')
        assert type_ == 'hg'
        assert name == 'test-repo'
        assert mode is 'auto'

    @pytest.mark.parametrize(
        'command', [
            'hg test-repo serve --stdio',
            'hg -R test-repo serve',
            'hg serve --stdio',
            'hg serve -R test-repo'
        ])
    def test_hg_command_not_matched(self, command, dummy_conf):
        wrapper = SshWrapper(command, 'auto', 'admin', '3', 'False', dummy_conf)
        type_, name, mode = wrapper.get_repo_details('auto')
        assert type_ is None
        assert name is None
        assert mode is 'auto'


class TestServe(object):
    def test_serve_raises_an_exception_when_vcs_is_not_recognized(self, dummy_conf):
        with mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.get_repo_store'):
            wrapper = SshWrapper('random command', 'auto', 'admin', '3', 'False', dummy_conf)

            with pytest.raises(Exception) as exc_info:
                wrapper.serve(
                    vcs='microsoft-tfs', repo='test-repo', mode=None, user='test',
                    permissions={})
            assert exc_info.value.message == 'Unrecognised VCS: microsoft-tfs'


class TestServeHg(object):

    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.invalidate_cache')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.get_user_permissions')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.get_repo_store')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.MercurialServer.run')
    def test_serve_creates_hg_instance(
            self, mercurial_run_mock, get_repo_store_mock, get_user_mock,
            invalidate_cache_mock, dummy_conf):

        repo_name = None
        mercurial_run_mock.return_value = 0, True
        get_user_mock.return_value = {repo_name: 'repository.admin'}
        get_repo_store_mock.return_value = {'path': '/tmp'}

        wrapper = SshWrapper('date', 'hg', 'admin', '3', 'False',
                             dummy_conf)
        exit_code = wrapper.wrap()
        assert exit_code == 0
        assert mercurial_run_mock.called

        assert get_repo_store_mock.called
        assert get_user_mock.called
        invalidate_cache_mock.assert_called_once_with(repo_name)

    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.invalidate_cache')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.get_user_permissions')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.get_repo_store')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.MercurialServer.run')
    def test_serve_hg_invalidates_cache(
            self, mercurial_run_mock, get_repo_store_mock, get_user_mock,
            invalidate_cache_mock, dummy_conf):

        repo_name = None
        mercurial_run_mock.return_value = 0, True
        get_user_mock.return_value = {repo_name: 'repository.admin'}
        get_repo_store_mock.return_value = {'path': '/tmp'}

        wrapper = SshWrapper('date', 'hg', 'admin', '3', 'False',
                             dummy_conf)
        exit_code = wrapper.wrap()
        assert exit_code == 0
        assert mercurial_run_mock.called

        assert get_repo_store_mock.called
        assert get_user_mock.called
        invalidate_cache_mock.assert_called_once_with(repo_name)


class TestServeGit(object):

    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.invalidate_cache')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.get_user_permissions')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.get_repo_store')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.GitServer.run')
    def test_serve_creates_git_instance(self, git_run_mock, get_repo_store_mock, get_user_mock,
            invalidate_cache_mock, dummy_conf):
        repo_name = None
        git_run_mock.return_value = 0, True
        get_user_mock.return_value = {repo_name: 'repository.admin'}
        get_repo_store_mock.return_value = {'path': '/tmp'}

        wrapper = SshWrapper('date', 'git', 'admin', '3', 'False',
                             dummy_conf)

        exit_code = wrapper.wrap()
        assert exit_code == 0
        assert git_run_mock.called
        assert get_repo_store_mock.called
        assert get_user_mock.called
        invalidate_cache_mock.assert_called_once_with(repo_name)

    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.invalidate_cache')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.get_user_permissions')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.get_repo_store')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.GitServer.run')
    def test_serve_git_invalidates_cache(
            self, git_run_mock, get_repo_store_mock, get_user_mock,
            invalidate_cache_mock, dummy_conf):
        repo_name = None
        git_run_mock.return_value = 0, True
        get_user_mock.return_value = {repo_name: 'repository.admin'}
        get_repo_store_mock.return_value = {'path': '/tmp'}

        wrapper = SshWrapper('date', 'git', 'admin', '3', 'False', dummy_conf)

        exit_code = wrapper.wrap()
        assert exit_code == 0
        assert git_run_mock.called

        assert get_repo_store_mock.called
        assert get_user_mock.called
        invalidate_cache_mock.assert_called_once_with(repo_name)


class TestServeSvn(object):

    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.invalidate_cache')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.get_user_permissions')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.RhodeCodeApiClient.get_repo_store')
    @mock.patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.SubversionServer.run')
    def test_serve_creates_svn_instance(
            self, svn_run_mock, get_repo_store_mock, get_user_mock,
            invalidate_cache_mock, dummy_conf):

        repo_name = None
        svn_run_mock.return_value = 0, True
        get_user_mock.return_value = {repo_name: 'repository.admin'}
        get_repo_store_mock.return_value = {'path': '/tmp'}

        wrapper = SshWrapper('date', 'svn', 'admin', '3', 'False', dummy_conf)

        exit_code = wrapper.wrap()
        assert exit_code == 0
        assert svn_run_mock.called

        assert get_repo_store_mock.called
        assert get_user_mock.called
        invalidate_cache_mock.assert_called_once_with(repo_name)
