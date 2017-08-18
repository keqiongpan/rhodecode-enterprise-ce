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
from mock import Mock, patch, call

from rhodecode.apps.ssh_support.lib.ssh_wrapper import SubversionServer


@pytest.fixture
def svn_server():
    return SubversionServerCreator()


class SubversionServerCreator(object):
    root = '/tmp/repo/path/'
    svn_path = '/usr/local/bin/svnserve'
    config_data = {
        'app:main': {
            'ssh.executable.svn': svn_path
        }
    }
    repo_name = 'test-svn'
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
            'user_permissions': {
                self.repo_name: 'repo_admin'
            },
            'config': self.config_mock,
        }
        parameters.update(kwargs)
        server = SubversionServer(**parameters)
        return server


class TestSubversionServer(object):
    def test_timeout_returns_value_from_config(self, svn_server):
        server = svn_server.create()
        assert server.timeout == 30

    @pytest.mark.parametrize(
        'permission', ['repository.admin', 'repository.write'])
    def test_check_permissions_with_write_permissions(
            self, svn_server, permission):
        user_permissions = {svn_server.repo_name: permission}
        server = svn_server.create(user_permissions=user_permissions)
        server.tunnel = Mock()
        server.repo_name = svn_server.repo_name
        result = server._check_permissions()
        assert result is True
        assert server.tunnel.read_only is False

    def test_check_permissions_with_read_permissions(self, svn_server):
        user_permissions = {svn_server.repo_name: 'repository.read'}
        server = svn_server.create(user_permissions=user_permissions)
        server.tunnel = Mock()
        server.repo_name = svn_server.repo_name
        result = server._check_permissions()
        assert result is True
        assert server.tunnel.read_only is True

    def test_check_permissions_with_no_permissions(self, svn_server, caplog):
        tunnel_mock = Mock()
        user_permissions = {}
        server = svn_server.create(user_permissions=user_permissions)
        server.tunnel = tunnel_mock
        server.repo_name = svn_server.repo_name
        result = server._check_permissions()
        assert result is False
        tunnel_mock.fail.assert_called_once_with(
            "Not enough permissions for repository {}".format(
                svn_server.repo_name))

    def test_run_returns_1_when_repository_name_cannot_be_extracted(
            self, svn_server):
        server = svn_server.create()
        with patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.SubversionTunnelWrapper') as tunnel_mock:
            tunnel_mock().get_first_client_response.return_value = None
            exit_code = server.run()
        assert exit_code == (1, False)
        tunnel_mock().fail.assert_called_once_with(
            'Repository name cannot be extracted')

    def test_run_returns_tunnel_return_code(self, svn_server, caplog):
        server = svn_server.create()
        fake_response = {
            'url': 'ssh+svn://test@example.com/test-svn/'
        }
        with patch('rhodecode.apps.ssh_support.lib.ssh_wrapper.SubversionTunnelWrapper') as tunnel_mock:
            with patch.object(server, '_check_permissions') as (
                    permissions_mock):
                permissions_mock.return_value = True
                tunnel = tunnel_mock()
                tunnel.get_first_client_response.return_value = fake_response
                tunnel.return_code = 0
                exit_code = server.run()
        permissions_mock.assert_called_once_with()

        expected_log_calls = sorted([
            "Using subversion binaries from '%s'" % svn_server.svn_path
        ])

        assert expected_log_calls == [t[2] for t in caplog.record_tuples]

        assert exit_code == (0, False)
        tunnel.patch_first_client_response.assert_called_once_with(
            fake_response)
        tunnel.sync.assert_called_once_with()
