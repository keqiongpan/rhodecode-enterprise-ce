# -*- coding: utf-8 -*-

# Copyright (C) 2016-2018 RhodeCode GmbH
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
import mock
import pytest

from rhodecode.apps.ssh_support.lib.backends.git import GitServer
from rhodecode.apps.ssh_support.tests.conftest import dummy_env, dummy_user


class GitServerCreator(object):
    root = '/tmp/repo/path/'
    git_path = '/usr/local/bin/git'
    config_data = {
        'app:main': {
            'ssh.executable.git': git_path,
            'vcs.hooks.protocol': 'http',
        }
    }
    repo_name = 'test_git'
    repo_mode = 'receive-pack'
    user = dummy_user()

    def __init__(self):
        def config_get(part, key):
            return self.config_data.get(part, {}).get(key)
        self.config_mock = mock.Mock()
        self.config_mock.get = mock.Mock(side_effect=config_get)

    def create(self, **kwargs):
        parameters = {
            'store': self.root,
            'ini_path': '',
            'user': self.user,
            'repo_name': self.repo_name,
            'repo_mode': self.repo_mode,
            'user_permissions': {
                self.repo_name: 'repository.admin'
            },
            'config': self.config_mock,
            'env': dummy_env()
        }
        parameters.update(kwargs)
        server = GitServer(**parameters)
        return server


@pytest.fixture
def git_server(app):
    return GitServerCreator()


class TestGitServer(object):

    def test_command(self, git_server):
        server = git_server.create()
        expected_command = (
            'cd {root}; {git_path} {repo_mode} \'{root}{repo_name}\''.format(
                root=git_server.root, git_path=git_server.git_path,
                repo_mode=git_server.repo_mode, repo_name=git_server.repo_name)
        )
        assert expected_command == server.tunnel.command()

    @pytest.mark.parametrize('permissions, action, code', [
        ({}, 'pull', -2),
        ({'test_git': 'repository.read'}, 'pull', 0),
        ({'test_git': 'repository.read'}, 'push', -2),
        ({'test_git': 'repository.write'}, 'push', 0),
        ({'test_git': 'repository.admin'}, 'push', 0),

    ])
    def test_permission_checks(self, git_server, permissions, action, code):
        server = git_server.create(user_permissions=permissions)
        result = server._check_permissions(action)
        assert result is code

    @pytest.mark.parametrize('permissions, value', [
        ({}, False),
        ({'test_git': 'repository.read'}, False),
        ({'test_git': 'repository.write'}, True),
        ({'test_git': 'repository.admin'}, True),

    ])
    def test_has_write_permissions(self, git_server, permissions, value):
        server = git_server.create(user_permissions=permissions)
        result = server.has_write_perm()
        assert result is value

    def test_run_returns_executes_command(self, git_server):
        server = git_server.create()
        from rhodecode.apps.ssh_support.lib.backends.git import GitTunnelWrapper
        with mock.patch.object(GitTunnelWrapper, 'create_hooks_env') as _patch:
            _patch.return_value = 0
            with mock.patch.object(GitTunnelWrapper, 'command', return_value='date'):
                exit_code = server.run()

        assert exit_code == (0, False)

    @pytest.mark.parametrize(
        'repo_mode, action', [
            ['receive-pack', 'push'],
            ['upload-pack', 'pull']
        ])
    def test_update_environment(self, git_server, repo_mode, action):
        server = git_server.create(repo_mode=repo_mode)
        with mock.patch('os.environ', {'SSH_CLIENT': '10.10.10.10 b'}):
            with mock.patch('os.putenv') as putenv_mock:
                server.update_environment(action)

        expected_data = {
            'username': git_server.user.username,
            'user_id': git_server.user.user_id,
            'scm': 'git',
            'repository': git_server.repo_name,
            'make_lock': None,
            'action': action,
            'ip': '10.10.10.10',
            'locked_by': [None, None],
            'config': '',
            'server_url': None,
            'hooks': ['push', 'pull'],
            'is_shadow_repo': False,
            'hooks_module': 'rhodecode.lib.hooks_daemon',
            'check_branch_perms': False,
            'detect_force_push': False,
            'user_agent': u'ssh-user-agent',
            'SSH': True,
            'SSH_PERMISSIONS': 'repository.admin',
        }
        args, kwargs = putenv_mock.call_args
        assert json.loads(args[1]) == expected_data
