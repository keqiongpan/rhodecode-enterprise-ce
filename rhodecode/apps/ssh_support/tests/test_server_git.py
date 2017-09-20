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

import json

import pytest
from mock import Mock, patch, call

from rhodecode.apps.ssh_support.lib.ssh_wrapper import GitServer


@pytest.fixture
def git_server():
    return GitServerCreator()


class GitServerCreator(object):
    root = '/tmp/repo/path/'
    git_path = '/usr/local/bin/'
    config_data = {
        'app:main': {
            'ssh.executable.git': git_path
        }
    }
    repo_name = 'test_git'
    repo_mode = 'receive-pack'
    user = 'vcs'

    def __init__(self):
        def config_get(part, key):
            return self.config_data.get(part, {}).get(key)
        self.config_mock = Mock()
        self.config_mock.get = Mock(side_effect=config_get)

    def create(self, **kwargs):
        parameters = {
            'store': {'path': self.root},
            'ini_path': '',
            'user': self.user,
            'repo_name': self.repo_name,
            'repo_mode': self.repo_mode,
            'user_permissions': {
                self.repo_name: 'repo_admin'
            },
            'config': self.config_mock,
        }
        parameters.update(kwargs)
        server = GitServer(**parameters)
        return server


class TestGitServer(object):
    def test_command(self, git_server):
        server = git_server.create()
        server.read_only = False
        expected_command = (
            'cd {root}; {git_path}-{repo_mode}'
            ' \'{root}{repo_name}\''.format(
                root=git_server.root, git_path=git_server.git_path,
                repo_mode=git_server.repo_mode, repo_name=git_server.repo_name)
        )
        assert expected_command == server.command

    def test_run_returns_exit_code_2_when_no_permissions(self, git_server, caplog):
        server = git_server.create()
        with patch.object(server, '_check_permissions') as permissions_mock:
            with patch.object(server, '_update_environment'):
                permissions_mock.return_value = 2
                exit_code = server.run()

        assert exit_code == (2, False)

    def test_run_returns_executes_command(self, git_server, caplog):
        server = git_server.create()
        with patch.object(server, '_check_permissions') as permissions_mock:
            with patch('os.system') as system_mock:
                with patch.object(server, '_update_environment') as (
                        update_mock):
                    permissions_mock.return_value = 0
                    system_mock.return_value = 0
                    exit_code = server.run()

        system_mock.assert_called_once_with(server.command)
        update_mock.assert_called_once_with()

        assert exit_code == (0, True)

    @pytest.mark.parametrize(
        'repo_mode, action', [
            ['receive-pack', 'push'],
            ['upload-pack', 'pull']
        ])
    def test_update_environment(self, git_server, repo_mode, action):
        server = git_server.create(repo_mode=repo_mode)
        with patch('os.environ', {'SSH_CLIENT': '10.10.10.10 b'}):
            with patch('os.putenv') as putenv_mock:
                server._update_environment()

        expected_data = {
            "username": git_server.user,
            "scm": "git",
            "repository": git_server.repo_name,
            "make_lock": None,
            "action": [action],
            "ip": "10.10.10.10",
            "locked_by": [None, None],
            "config": ""
        }
        args, kwargs = putenv_mock.call_args
        assert json.loads(args[1]) == expected_data


class TestGitServerCheckPermissions(object):
    def test_returns_2_when_no_permissions_found(self, git_server, caplog):
        user_permissions = {}
        server = git_server.create(user_permissions=user_permissions)
        result = server._check_permissions()
        assert result == 2

        log_msg = 'permission for vcs on test_git are: None'
        assert log_msg in [t[2] for t in caplog.record_tuples]

    def test_returns_2_when_no_permissions(self, git_server, caplog):
        user_permissions = {git_server.repo_name: 'repository.none'}
        server = git_server.create(user_permissions=user_permissions)
        result = server._check_permissions()
        assert result == 2

        log_msg = 'repo not found or no permissions'
        assert log_msg in [t[2] for t in caplog.record_tuples]

    @pytest.mark.parametrize(
        'permission', ['repository.admin', 'repository.write'])
    def test_access_allowed_when_user_has_write_permissions(
            self, git_server, permission, caplog):
        user_permissions = {git_server.repo_name: permission}
        server = git_server.create(user_permissions=user_permissions)
        result = server._check_permissions()
        assert result is None

        log_msg = 'Write Permissions for User "%s" granted to repo "%s"!' % (
            git_server.user, git_server.repo_name)
        assert log_msg in [t[2] for t in caplog.record_tuples]

    def test_write_access_is_not_allowed_when_user_has_read_permission(
            self, git_server, caplog):
        user_permissions = {git_server.repo_name: 'repository.read'}
        server = git_server.create(
            user_permissions=user_permissions, repo_mode='receive-pack')
        result = server._check_permissions()
        assert result == -3

        log_msg = 'Only Read Only access for User "%s" granted to repo "%s"! Failing!' % (
            git_server.user, git_server.repo_name)
        assert log_msg in [t[2] for t in caplog.record_tuples]

    def test_read_access_allowed_when_user_has_read_permission(
            self, git_server, caplog):
        user_permissions = {git_server.repo_name: 'repository.read'}
        server = git_server.create(
            user_permissions=user_permissions, repo_mode='upload-pack')
        result = server._check_permissions()
        assert result is None

        log_msg = 'Only Read Only access for User "%s" granted to repo "%s"!' % (
            git_server.user, git_server.repo_name)
        assert log_msg in [t[2] for t in caplog.record_tuples]

    def test_returns_error_when_permission_not_recognised(
            self, git_server, caplog):
        user_permissions = {git_server.repo_name: 'repository.whatever'}
        server = git_server.create(
            user_permissions=user_permissions, repo_mode='upload-pack')
        result = server._check_permissions()
        assert result == -2

        log_msg = 'Cannot properly fetch user permission. ' \
                  'Return value is: repository.whatever'
        assert log_msg in [t[2] for t in caplog.record_tuples]