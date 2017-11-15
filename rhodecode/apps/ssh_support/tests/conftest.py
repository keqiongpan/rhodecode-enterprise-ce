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
import pytest
from pyramid.compat import configparser

from rhodecode.apps.ssh_support.lib.ssh_wrapper import SshWrapper
from rhodecode.lib.utils2 import AttributeDict


@pytest.fixture
def dummy_conf_file(tmpdir):
    conf = configparser.ConfigParser()
    conf.add_section('app:main')
    conf.set('app:main', 'ssh.executable.hg', '/usr/bin/hg')
    conf.set('app:main', 'ssh.executable.git', '/usr/bin/git')
    conf.set('app:main', 'ssh.executable.svn', '/usr/bin/svnserve')

    f_path = os.path.join(str(tmpdir), 'ssh_wrapper_test.ini')
    with open(f_path, 'wb') as f:
        conf.write(f)

    return os.path.join(f_path)


@pytest.fixture
def dummy_env():
    return {
        'request':
            AttributeDict(host_url='http://localhost', script_name='/')
    }


@pytest.fixture
def dummy_user():
    return AttributeDict(username='test_user')


@pytest.fixture
def ssh_wrapper(app, dummy_conf_file, dummy_env):
    conn_info = '127.0.0.1 22 10.0.0.1 443'
    return SshWrapper(
        'random command', conn_info, 'auto', 'admin', '1', key_id='1',
        shell=False, ini_path=dummy_conf_file, env=dummy_env)
