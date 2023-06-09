# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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
import platform
import socket

import pytest

from rhodecode.lib.pyramid_utils import get_app_config
from rhodecode.tests.fixture import TestINI
from rhodecode.tests.server_utils import RcVCSServer


def _parse_json(value):
    return json.loads(value) if value else None


def pytest_addoption(parser):
    parser.addoption(
        '--test-loglevel', dest='test_loglevel',
        help="Set default Logging level for tests, warn (default), info, debug")
    group = parser.getgroup('pylons')
    group.addoption(
        '--with-pylons', dest='pyramid_config',
        help="Set up a Pylons environment with the specified config file.")
    group.addoption(
        '--ini-config-override', action='store', type=_parse_json,
        default=None, dest='pyramid_config_override', help=(
            "Overrides the .ini file settings. Should be specified in JSON"
            " format, e.g. '{\"section\": {\"parameter\": \"value\", ...}}'"
        )
    )
    parser.addini(
        'pyramid_config',
        "Set up a Pyramid environment with the specified config file.")

    vcsgroup = parser.getgroup('vcs')
    vcsgroup.addoption(
        '--without-vcsserver', dest='with_vcsserver', action='store_false',
        help="Do not start the VCSServer in a background process.")
    vcsgroup.addoption(
        '--with-vcsserver-http', dest='vcsserver_config_http',
        help="Start the HTTP VCSServer with the specified config file.")
    vcsgroup.addoption(
        '--vcsserver-protocol', dest='vcsserver_protocol',
        help="Start the VCSServer with HTTP protocol support.")
    vcsgroup.addoption(
        '--vcsserver-config-override', action='store', type=_parse_json,
        default=None, dest='vcsserver_config_override', help=(
            "Overrides the .ini file settings for the VCSServer. "
            "Should be specified in JSON "
            "format, e.g. '{\"section\": {\"parameter\": \"value\", ...}}'"
        )
    )
    vcsgroup.addoption(
        '--vcsserver-port', action='store', type=int,
        default=None, help=(
            "Allows to set the port of the vcsserver. Useful when testing "
            "against an already running server and random ports cause "
            "trouble."))
    parser.addini(
        'vcsserver_config_http',
        "Start the HTTP VCSServer with the specified config file.")
    parser.addini(
        'vcsserver_protocol',
        "Start the VCSServer with HTTP protocol support.")


@pytest.fixture(scope='session')
def vcsserver(request, vcsserver_port, vcsserver_factory):
    """
    Session scope VCSServer.

    Tests wich need the VCSServer have to rely on this fixture in order
    to ensure it will be running.

    For specific needs, the fixture vcsserver_factory can be used. It allows to
    adjust the configuration file for the test run.

    Command line args:

    --without-vcsserver: Allows to switch this fixture off. You have to
    manually start the server.

    --vcsserver-port: Will expect the VCSServer to listen on this port.
    """

    if not request.config.getoption('with_vcsserver'):
        return None

    return vcsserver_factory(
        request, vcsserver_port=vcsserver_port)


@pytest.fixture(scope='session')
def vcsserver_factory(tmpdir_factory):
    """
    Use this if you need a running vcsserver with a special configuration.
    """

    def factory(request, overrides=(), vcsserver_port=None,
                log_file=None):

        if vcsserver_port is None:
            vcsserver_port = get_available_port()

        overrides = list(overrides)
        overrides.append({'server:main': {'port': vcsserver_port}})

        option_name = 'vcsserver_config_http'
        override_option_name = 'vcsserver_config_override'
        config_file = get_config(
            request.config, option_name=option_name,
            override_option_name=override_option_name, overrides=overrides,
            basetemp=tmpdir_factory.getbasetemp().strpath,
            prefix='test_vcs_')

        server = RcVCSServer(config_file, log_file)
        server.start()

        @request.addfinalizer
        def cleanup():
            server.shutdown()

        server.wait_until_ready()
        return server

    return factory


def is_cygwin():
    return 'cygwin' in platform.system().lower()


def _use_log_level(config):
    level = config.getoption('test_loglevel') or 'warn'
    return level.upper()


@pytest.fixture(scope='session')
def ini_config(request, tmpdir_factory, rcserver_port, vcsserver_port):
    option_name = 'pyramid_config'
    log_level = _use_log_level(request.config)

    overrides = [
        {'server:main': {'port': rcserver_port}},
        {'app:main': {
            'vcs.server': 'localhost:%s' % vcsserver_port,
            # johbo: We will always start the VCSServer on our own based on the
            # fixtures of the test cases. For the test run it must always be
            # off in the INI file.
            'vcs.start_server': 'false',

            'vcs.server.protocol': 'http',
            'vcs.scm_app_implementation': 'http',
            'vcs.hooks.protocol': 'http',
            'vcs.hooks.host': '127.0.0.1',
        }},

        {'handler_console': {
            'class ': 'StreamHandler',
            'args ': '(sys.stderr,)',
            'level': log_level,
        }},

    ]

    filename = get_config(
        request.config, option_name=option_name,
        override_option_name='{}_override'.format(option_name),
        overrides=overrides,
        basetemp=tmpdir_factory.getbasetemp().strpath,
        prefix='test_rce_')
    return filename


@pytest.fixture(scope='session')
def ini_settings(ini_config):
    ini_path = ini_config
    return get_app_config(ini_path)


def get_available_port():
    family = socket.AF_INET
    socktype = socket.SOCK_STREAM
    host = '127.0.0.1'

    mysocket = socket.socket(family, socktype)
    mysocket.bind((host, 0))
    port = mysocket.getsockname()[1]
    mysocket.close()
    del mysocket
    return port


@pytest.fixture(scope='session')
def rcserver_port(request):
    port = get_available_port()
    print('Using rcserver port {}'.format(port))
    return port


@pytest.fixture(scope='session')
def vcsserver_port(request):
    port = request.config.getoption('--vcsserver-port')
    if port is None:
        port = get_available_port()
        print('Using vcsserver port {}'.format(port))
    return port


@pytest.fixture(scope='session')
def available_port_factory():
    """
    Returns a callable which returns free port numbers.
    """
    return get_available_port


@pytest.fixture()
def available_port(available_port_factory):
    """
    Gives you one free port for the current test.

    Uses "available_port_factory" to retrieve the port.
    """
    return available_port_factory()


@pytest.fixture(scope='session')
def testini_factory(tmpdir_factory, ini_config):
    """
    Factory to create an INI file based on TestINI.

    It will make sure to place the INI file in the correct directory.
    """
    basetemp = tmpdir_factory.getbasetemp().strpath
    return TestIniFactory(basetemp, ini_config)


class TestIniFactory(object):

    def __init__(self, basetemp, template_ini):
        self._basetemp = basetemp
        self._template_ini = template_ini

    def __call__(self, ini_params, new_file_prefix='test'):
        ini_file = TestINI(
            self._template_ini, ini_params=ini_params,
            new_file_prefix=new_file_prefix, dir=self._basetemp)
        result = ini_file.create()
        return result


def get_config(
        config, option_name, override_option_name, overrides=None,
        basetemp=None, prefix='test'):
    """
    Find a configuration file and apply overrides for the given `prefix`.
    """
    config_file = (
        config.getoption(option_name) or config.getini(option_name))
    if not config_file:
        pytest.exit(
            "Configuration error, could not extract {}.".format(option_name))

    overrides = overrides or []
    config_override = config.getoption(override_option_name)
    if config_override:
        overrides.append(config_override)
    temp_ini_file = TestINI(
        config_file, ini_params=overrides, new_file_prefix=prefix,
        dir=basetemp)

    return temp_ini_file.create()
