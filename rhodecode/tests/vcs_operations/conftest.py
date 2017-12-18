# -*- coding: utf-8 -*-

# Copyright (C) 2010-2017 RhodeCode GmbH
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

"""
py.test config for test suite for making push/pull operations.

.. important::

   You must have git >= 1.8.5 for tests to work fine. With 68b939b git started
   to redirect things to stderr instead of stdout.
"""

import ConfigParser
import os
import subprocess32
import tempfile
import textwrap
import pytest

import rhodecode
from rhodecode.model.db import Repository
from rhodecode.model.meta import Session
from rhodecode.model.settings import SettingsModel
from rhodecode.tests import (
    GIT_REPO, HG_REPO, TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS,)
from rhodecode.tests.fixture import Fixture
from rhodecode.tests.utils import is_url_reachable, wait_for_url

RC_LOG = os.path.join(tempfile.gettempdir(), 'rc.log')
REPO_GROUP = 'a_repo_group'
HG_REPO_WITH_GROUP = '%s/%s' % (REPO_GROUP, HG_REPO)
GIT_REPO_WITH_GROUP = '%s/%s' % (REPO_GROUP, GIT_REPO)


def assert_no_running_instance(url):
    if is_url_reachable(url):
        print("Hint: Usually this means another instance of Enterprise "
              "is running in the background.")
        pytest.fail(
            "Port is not free at %s, cannot start web interface" % url)


def get_port(pyramid_config):
    config = ConfigParser.ConfigParser()
    config.read(pyramid_config)
    return config.get('server:main', 'port')


def get_host_url(pyramid_config):
    """Construct the host url using the port in the test configuration."""
    return '127.0.0.1:%s' % get_port(pyramid_config)


class RcWebServer(object):
    """
    Represents a running RCE web server used as a test fixture.
    """
    def __init__(self, pyramid_config, log_file):
        self.pyramid_config = pyramid_config
        self.log_file = log_file

    def repo_clone_url(self, repo_name, **kwargs):
        params = {
            'user': TEST_USER_ADMIN_LOGIN,
            'passwd': TEST_USER_ADMIN_PASS,
            'host': get_host_url(self.pyramid_config),
            'cloned_repo': repo_name,
        }
        params.update(**kwargs)
        _url = 'http://%(user)s:%(passwd)s@%(host)s/%(cloned_repo)s' % params
        return _url

    def host_url(self):
        return 'http://' + get_host_url(self.pyramid_config)

    def get_rc_log(self):
        with open(self.log_file) as f:
            return f.read()


@pytest.fixture(scope="module")
def rcextensions(request, baseapp, tmpdir_factory):
    """
    Installs a testing rcextensions pack to ensure they work as expected.
    """
    init_content = textwrap.dedent("""
        # Forward import the example rcextensions to make it
        # active for our tests.
        from rhodecode.tests.other.example_rcextensions import *
    """)

    # Note: rcextensions are looked up based on the path of the ini file
    root_path = tmpdir_factory.getbasetemp()
    rcextensions_path = root_path.join('rcextensions')
    init_path = rcextensions_path.join('__init__.py')

    if rcextensions_path.check():
        pytest.fail(
            "Path for rcextensions already exists, please clean up before "
            "test run this path: %s" % (rcextensions_path, ))
        return

    request.addfinalizer(rcextensions_path.remove)
    init_path.write_binary(init_content, ensure=True)


@pytest.fixture(scope="module")
def repos(request, baseapp):
    """Create a copy of each test repo in a repo group."""
    fixture = Fixture()
    repo_group = fixture.create_repo_group(REPO_GROUP)
    repo_group_id = repo_group.group_id
    fixture.create_fork(HG_REPO, HG_REPO,
                        repo_name_full=HG_REPO_WITH_GROUP,
                        repo_group=repo_group_id)
    fixture.create_fork(GIT_REPO, GIT_REPO,
                        repo_name_full=GIT_REPO_WITH_GROUP,
                        repo_group=repo_group_id)

    @request.addfinalizer
    def cleanup():
        fixture.destroy_repo(HG_REPO_WITH_GROUP)
        fixture.destroy_repo(GIT_REPO_WITH_GROUP)
        fixture.destroy_repo_group(repo_group_id)


@pytest.fixture(scope="session")
def vcs_server_config_override():
    return ({'server:main': {'workers': 2}},)


@pytest.fixture(scope="module")
def rc_web_server_config(testini_factory):
    """
    Configuration file used for the fixture `rc_web_server`.
    """
    CUSTOM_PARAMS = [
        {'handler_console': {'level': 'DEBUG'}},
    ]
    return testini_factory(CUSTOM_PARAMS)


@pytest.fixture(scope="module")
def rc_web_server(
        request, baseapp, rc_web_server_config, repos, rcextensions):
    """
    Run the web server as a subprocess.

    Since we have already a running vcsserver, this is not spawned again.
    """
    env = os.environ.copy()
    env['RC_NO_TMP_PATH'] = '1'

    rc_log = list(RC_LOG.partition('.log'))
    rc_log.insert(1, get_port(rc_web_server_config))
    rc_log = ''.join(rc_log)

    server_out = open(rc_log, 'w')

    host_url = 'http://' + get_host_url(rc_web_server_config)
    assert_no_running_instance(host_url)
    command = ['gunicorn', '--worker-class', 'gevent', '--paste', rc_web_server_config]

    print('rhodecode-web starting at: {}'.format(host_url))
    print('rhodecode-web command: {}'.format(command))
    print('rhodecode-web logfile: {}'.format(rc_log))

    proc = subprocess32.Popen(
        command, bufsize=0, env=env, stdout=server_out, stderr=server_out)

    wait_for_url(host_url, timeout=30)

    @request.addfinalizer
    def stop_web_server():
        # TODO: Find out how to integrate with the reporting of py.test to
        # make this information available.
        print("\nServer log file written to %s" % (rc_log, ))
        proc.kill()
        server_out.flush()
        server_out.close()

    return RcWebServer(rc_web_server_config, log_file=rc_log)


@pytest.fixture
def disable_locking(baseapp):
    r = Repository.get_by_repo_name(GIT_REPO)
    Repository.unlock(r)
    r.enable_locking = False
    Session().add(r)
    Session().commit()

    r = Repository.get_by_repo_name(HG_REPO)
    Repository.unlock(r)
    r.enable_locking = False
    Session().add(r)
    Session().commit()


@pytest.fixture
def enable_auth_plugins(request, baseapp, csrf_token):
    """
    Return a factory object that when called, allows to control which
    authentication plugins are enabled.
    """
    def _enable_plugins(plugins_list, override=None):
        override = override or {}
        params = {
            'auth_plugins': ','.join(plugins_list),
        }

        # helper translate some names to others
        name_map = {
            'token': 'authtoken'
        }

        for module in plugins_list:
            plugin_name = module.partition('#')[-1]
            if plugin_name in name_map:
                plugin_name = name_map[plugin_name]
            enabled_plugin = 'auth_%s_enabled' % plugin_name
            cache_ttl = 'auth_%s_cache_ttl' % plugin_name

            # default params that are needed for each plugin,
            # `enabled` and `cache_ttl`
            params.update({
                enabled_plugin: True,
                cache_ttl: 0
            })
            if override.get:
                params.update(override.get(module, {}))

            validated_params = params
            for k, v in validated_params.items():
                setting = SettingsModel().create_or_update_setting(k, v)
                Session().add(setting)
            Session().commit()

    def cleanup():
        _enable_plugins(['egg:rhodecode-enterprise-ce#rhodecode'])

    request.addfinalizer(cleanup)

    return _enable_plugins


@pytest.fixture
def fs_repo_only(request, rhodecode_fixtures):
    def fs_repo_fabric(repo_name, repo_type):
        rhodecode_fixtures.create_repo(repo_name, repo_type=repo_type)
        rhodecode_fixtures.destroy_repo(repo_name, fs_remove=False)

        def cleanup():
            rhodecode_fixtures.destroy_repo(repo_name, fs_remove=True)
            rhodecode_fixtures.destroy_repo_on_filesystem(repo_name)

        request.addfinalizer(cleanup)

    return fs_repo_fabric
