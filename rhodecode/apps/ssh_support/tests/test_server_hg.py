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

import pytest
from mock import Mock, patch

from rhodecode.apps.ssh_support.lib.backends.hg import MercurialServer


@pytest.fixture
def hg_server():
    return MercurialServerCreator()


class MercurialServerCreator(object):
    root = '/tmp/repo/path/'
    hg_path = '/usr/local/bin/hg'

    config_data = {
        'app:main': {
            'ssh.executable.hg': hg_path
        }
    }
    repo_name = 'test_hg'
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
            'user_permissions': {
                'test_hg': 'repo_admin'
            },
            'config': self.config_mock,
        }
        parameters.update(kwargs)
        server = MercurialServer(**parameters)
        return server


class TestMercurialServer(object):
    def test_read_only_command(self, hg_server):
        server = hg_server.create()
        server.read_only = True
        expected_command = (
            'cd {root}; {hg_path} -R {root}{repo_name} serve --stdio'
            ' --config hooks.pretxnchangegroup="false"'.format(
                root=hg_server.root, hg_path=hg_server.hg_path,
                repo_name=hg_server.repo_name)
        )
        assert expected_command == server.command

    def test_normal_command(self, hg_server):
        server = hg_server.create()
        server.read_only = False
        expected_command = (
            'cd {root}; {hg_path} -R {root}{repo_name} serve --stdio '.format(
                root=hg_server.root, hg_path=hg_server.hg_path,
                repo_name=hg_server.repo_name)
        )
        assert expected_command == server.command

    def test_access_rejected_when_permissions_are_not_found(self, hg_server, caplog):
        user_permissions = {}
        server = hg_server.create(user_permissions=user_permissions)
        result = server._check_permissions()
        assert result is False

        log_msg = 'repo not found or no permissions'
        assert log_msg in [t[2] for t in caplog.record_tuples]

    def test_access_rejected_when_no_permissions(self, hg_server, caplog):
        user_permissions = {hg_server.repo_name: 'repository.none'}
        server = hg_server.create(user_permissions=user_permissions)
        result = server._check_permissions()
        assert result is False

        log_msg = 'repo not found or no permissions'
        assert log_msg in [t[2] for t in caplog.record_tuples]

    @pytest.mark.parametrize(
        'permission', ['repository.admin', 'repository.write'])
    def test_access_allowed_when_user_has_write_permissions(
            self, hg_server, permission, caplog):
        user_permissions = {hg_server.repo_name: permission}
        server = hg_server.create(user_permissions=user_permissions)
        result = server._check_permissions()
        assert result is True

        assert server.read_only is False
        log_msg = 'Write Permissions for User "vcs" granted to repo "test_hg"!'
        assert log_msg in [t[2] for t in caplog.record_tuples]

    def test_access_allowed_when_user_has_read_permissions(self, hg_server, caplog):
        user_permissions = {hg_server.repo_name: 'repository.read'}
        server = hg_server.create(user_permissions=user_permissions)
        result = server._check_permissions()
        assert result is True

        assert server.read_only is True
        log_msg = 'Only Read Only access for User "%s" granted to repo "%s"!' % (
            hg_server.user, hg_server.repo_name)
        assert log_msg in [t[2] for t in caplog.record_tuples]

    def test_run_returns_exit_code_2_when_no_permissions(self, hg_server, caplog):
        server = hg_server.create()
        with patch.object(server, '_check_permissions') as permissions_mock:
            permissions_mock.return_value = False
            exit_code = server.run()
            assert exit_code == (2, False)

    def test_run_returns_executes_command(self, hg_server, caplog):
        server = hg_server.create()
        with patch.object(server, '_check_permissions') as permissions_mock:
            with patch('os.system') as system_mock:
                permissions_mock.return_value = True
                system_mock.return_value = 0
                exit_code = server.run()

        system_mock.assert_called_once_with(server.command)
        assert exit_code == (0, False)
