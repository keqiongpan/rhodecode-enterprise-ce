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

import pytest


class TestSSHWrapper(object):

    def test_serve_raises_an_exception_when_vcs_is_not_recognized(self, ssh_wrapper):
        with pytest.raises(Exception) as exc_info:
            ssh_wrapper.serve(
                vcs='microsoft-tfs', repo='test-repo', mode=None, user='test',
                permissions={}, branch_permissions={})
        assert exc_info.value.message == 'Unrecognised VCS: microsoft-tfs'

    def test_parse_config(self, ssh_wrapper):
        config = ssh_wrapper.parse_config(ssh_wrapper.ini_path)
        assert config

    def test_get_connection_info(self, ssh_wrapper):
        conn_info = ssh_wrapper.get_connection_info()
        assert {'client_ip': '127.0.0.1',
                'client_port': '22',
                'server_ip': '10.0.0.1',
                'server_port': '443'} == conn_info

    @pytest.mark.parametrize('command, vcs', [
        ('xxx', None),
        ('svnserve -t', 'svn'),
        ('hg -R repo serve --stdio', 'hg'),
        ('git-receive-pack \'repo.git\'', 'git'),

    ])
    def test_get_repo_details(self, ssh_wrapper, command, vcs):
        ssh_wrapper.command = command
        vcs_type, repo_name, mode = ssh_wrapper.get_repo_details(mode='auto')
        assert vcs_type == vcs
