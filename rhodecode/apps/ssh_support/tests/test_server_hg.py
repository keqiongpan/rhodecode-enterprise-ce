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

import mock
import pytest

from rhodecode.apps.ssh_support.lib.backends.hg import MercurialServer
from rhodecode.apps.ssh_support.tests.conftest import dummy_env, dummy_user


class MercurialServerCreator(object):
    root = '/tmp/repo/path/'
    hg_path = '/usr/local/bin/hg'

    config_data = {
        'app:main': {
            'ssh.executable.hg': hg_path,
            'vcs.hooks.protocol': 'http',
        }
    }
    repo_name = 'test_hg'
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
            'user_permissions': {
                'test_hg': 'repository.admin'
            },
            'config': self.config_mock,
            'env': dummy_env()
        }
        parameters.update(kwargs)
        server = MercurialServer(**parameters)
        return server


@pytest.fixture
def hg_server(app):
    return MercurialServerCreator()


class TestMercurialServer(object):

    def test_command(self, hg_server):
        server = hg_server.create()
        expected_command = (
            'cd {root}; {hg_path} -R {root}{repo_name} serve --stdio'.format(
                root=hg_server.root, hg_path=hg_server.hg_path,
                repo_name=hg_server.repo_name)
        )
        assert expected_command == server.tunnel.command()

    @pytest.mark.parametrize('permissions, action, code', [
        ({}, 'pull', -2),
        ({'test_hg': 'repository.read'}, 'pull', 0),
        ({'test_hg': 'repository.read'}, 'push', -2),
        ({'test_hg': 'repository.write'}, 'push', 0),
        ({'test_hg': 'repository.admin'}, 'push', 0),

    ])
    def test_permission_checks(self, hg_server, permissions, action, code):
        server = hg_server.create(user_permissions=permissions)
        result = server._check_permissions(action)
        assert result is code

    @pytest.mark.parametrize('permissions, value', [
        ({}, False),
        ({'test_hg': 'repository.read'}, False),
        ({'test_hg': 'repository.write'}, True),
        ({'test_hg': 'repository.admin'}, True),

    ])
    def test_has_write_permissions(self, hg_server, permissions, value):
        server = hg_server.create(user_permissions=permissions)
        result = server.has_write_perm()
        assert result is value

    def test_run_returns_executes_command(self, hg_server):
        server = hg_server.create()
        from rhodecode.apps.ssh_support.lib.backends.hg import MercurialTunnelWrapper
        with mock.patch.object(MercurialTunnelWrapper, 'create_hooks_env') as _patch:
            _patch.return_value = 0
            with mock.patch.object(MercurialTunnelWrapper, 'command', return_value='date'):
                exit_code = server.run()

        assert exit_code == (0, False)



