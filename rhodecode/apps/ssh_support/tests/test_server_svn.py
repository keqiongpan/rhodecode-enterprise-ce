# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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

from rhodecode.apps.ssh_support.lib.backends.svn import SubversionServer
from rhodecode.apps.ssh_support.tests.conftest import plain_dummy_env, plain_dummy_user


class SubversionServerCreator(object):
    root = '/tmp/repo/path/'
    svn_path = '/usr/local/bin/svnserve'
    config_data = {
        'app:main': {
            'ssh.executable.svn': svn_path,
            'vcs.hooks.protocol': 'http',
        }
    }
    repo_name = 'test-svn'
    user = plain_dummy_user()

    def __init__(self):
        def config_get(part, key):
            return self.config_data.get(part, {}).get(key)
        self.config_mock = mock.Mock()
        self.config_mock.get = mock.Mock(side_effect=config_get)

    def create(self, **kwargs):
        parameters = {
            'store': self.root,
            'repo_name': self.repo_name,
            'ini_path': '',
            'user': self.user,
            'user_permissions': {
                self.repo_name: 'repository.admin'
            },
            'config': self.config_mock,
            'env': plain_dummy_env()
        }

        parameters.update(kwargs)
        server = SubversionServer(**parameters)
        return server


@pytest.fixture()
def svn_server(app):
    return SubversionServerCreator()


class TestSubversionServer(object):
    def test_command(self, svn_server):
        server = svn_server.create()
        expected_command = [
            svn_server.svn_path, '-t',
            '--config-file', server.tunnel.svn_conf_path,
            '--tunnel-user', svn_server.user.username,
            '-r', svn_server.root
        ]

        assert expected_command == server.tunnel.command()

    @pytest.mark.parametrize('permissions, action, code', [
        ({}, 'pull', -2),
        ({'test-svn': 'repository.read'}, 'pull', 0),
        ({'test-svn': 'repository.read'}, 'push', -2),
        ({'test-svn': 'repository.write'}, 'push', 0),
        ({'test-svn': 'repository.admin'}, 'push', 0),

    ])
    def test_permission_checks(self, svn_server, permissions, action, code):
        server = svn_server.create(user_permissions=permissions)
        result = server._check_permissions(action)
        assert result is code

    @pytest.mark.parametrize('permissions, access_paths, expected_match', [
        # not matched repository name
        ({
             'test-svn': ''
         }, ['test-svn-1', 'test-svn-1/subpath'],
         None),

        # exact match
        ({
             'test-svn': ''
         },
         ['test-svn'],
         'test-svn'),

        # subdir commits
        ({
             'test-svn': ''
         },
         ['test-svn/foo',
          'test-svn/foo/test-svn',
          'test-svn/trunk/development.txt',
          ],
         'test-svn'),

        # subgroups + similar patterns
        ({
             'test-svn': '',
             'test-svn-1': '',
             'test-svn-subgroup/test-svn': '',

         },
         ['test-svn-1',
          'test-svn-1/foo/test-svn',
          'test-svn-1/test-svn',
          ],
         'test-svn-1'),

        # subgroups + similar patterns
        ({
             'test-svn-1': '',
             'test-svn-10': '',
             'test-svn-100': '',
         },
         ['test-svn-10',
          'test-svn-10/foo/test-svn',
          'test-svn-10/test-svn',
          ],
         'test-svn-10'),

        # subgroups + similar patterns
        ({
             'name': '',
             'nameContains': '',
             'nameContainsThis': '',
         },
         ['nameContains',
          'nameContains/This',
          'nameContains/This/test-svn',
          ],
         'nameContains'),

        # subgroups + similar patterns
        ({
             'test-svn': '',
             'test-svn-1': '',
             'test-svn-subgroup/test-svn': '',

         },
         ['test-svn-subgroup/test-svn',
          'test-svn-subgroup/test-svn/foo/test-svn',
          'test-svn-subgroup/test-svn/trunk/example.txt',
          ],
         'test-svn-subgroup/test-svn'),
    ])
    def test_repo_extraction_on_subdir(self, svn_server, permissions, access_paths, expected_match):
        server = svn_server.create(user_permissions=permissions)
        for path in access_paths:
            repo_name = server.tunnel._match_repo_name(path)
            assert repo_name == expected_match

    def test_run_returns_executes_command(self, svn_server):
        server = svn_server.create()
        from rhodecode.apps.ssh_support.lib.backends.svn import SubversionTunnelWrapper
        os.environ['SSH_CLIENT'] = '127.0.0.1'
        with mock.patch.object(
                SubversionTunnelWrapper, 'get_first_client_response',
                return_value={'url': 'http://server/test-svn'}):
            with mock.patch.object(
                    SubversionTunnelWrapper, 'patch_first_client_response',
                    return_value=0):
                with mock.patch.object(
                        SubversionTunnelWrapper, 'sync',
                        return_value=0):
                    with mock.patch.object(
                            SubversionTunnelWrapper, 'command',
                            return_value=['date']):

                        exit_code = server.run()
        # SVN has this differently configured, and we get in our mock env
        # None as return code
        assert exit_code == (None, False)

    def test_run_returns_executes_command_that_cannot_extract_repo_name(self, svn_server):
        server = svn_server.create()
        from rhodecode.apps.ssh_support.lib.backends.svn import SubversionTunnelWrapper
        with mock.patch.object(
                SubversionTunnelWrapper, 'command',
                return_value=['date']):
            with mock.patch.object(
                    SubversionTunnelWrapper, 'get_first_client_response',
                    return_value=None):
                    exit_code = server.run()

        assert exit_code == (1, False)
