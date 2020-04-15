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
import pytest
import mock

from rhodecode.apps.ssh_support import utils
from rhodecode.lib.utils2 import AttributeDict


class TestSshKeyFileGeneration(object):
    @pytest.mark.parametrize('ssh_wrapper_cmd', ['/tmp/sshwrapper.py'])
    @pytest.mark.parametrize('allow_shell', [True, False])
    @pytest.mark.parametrize('debug', [True, False])
    @pytest.mark.parametrize('ssh_opts', [None, 'mycustom,option'])
    def test_write_keyfile(self, tmpdir, ssh_wrapper_cmd, allow_shell, debug, ssh_opts):

        authorized_keys_file_path = os.path.join(str(tmpdir), 'authorized_keys')

        def keys():
            return [
                AttributeDict({'user': AttributeDict(username='admin'),
                               'ssh_key_data': 'ssh-rsa ADMIN_KEY'}),
                AttributeDict({'user': AttributeDict(username='user'),
                               'ssh_key_data': 'ssh-rsa USER_KEY'}),
            ]
        with mock.patch('rhodecode.apps.ssh_support.utils.get_all_active_keys',
                        return_value=keys()):
            with mock.patch.dict('rhodecode.CONFIG', {'__file__': '/tmp/file.ini'}):
                utils._generate_ssh_authorized_keys_file(
                    authorized_keys_file_path, ssh_wrapper_cmd,
                    allow_shell, ssh_opts, debug
                )

                assert os.path.isfile(authorized_keys_file_path)
                with open(authorized_keys_file_path) as f:
                    content = f.read()

                    assert 'command="/tmp/sshwrapper.py' in content
                    assert 'This file is managed by RhodeCode, ' \
                           'please do not edit it manually.' in content

                    if allow_shell:
                        assert '--shell' in content

                    if debug:
                        assert '--debug' in content

                    assert '--user' in content
                    assert '--user-id' in content

                    if ssh_opts:
                        assert ssh_opts in content
