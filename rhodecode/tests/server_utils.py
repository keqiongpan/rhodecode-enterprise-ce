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


import os
import time
import tempfile
import pytest
import subprocess32
import configobj

from urllib2 import urlopen, URLError
from pyramid.compat import configparser


from rhodecode.tests import TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS
from rhodecode.tests.utils import is_url_reachable


def get_port(pyramid_config):
    config = configparser.ConfigParser()
    config.read(pyramid_config)
    return config.get('server:main', 'port')


def get_host_url(pyramid_config):
    """Construct the host url using the port in the test configuration."""
    return '127.0.0.1:%s' % get_port(pyramid_config)


def assert_no_running_instance(url):
    if is_url_reachable(url):
        print("Hint: Usually this means another instance of server "
              "is running in the background at %s." % url)
        pytest.fail(
            "Port is not free at %s, cannot start server at" % url)


class ServerBase(object):
    _args = []
    log_file_name = 'NOT_DEFINED.log'
    status_url_tmpl = 'http://{host}:{port}'

    def __init__(self, config_file, log_file):
        self.config_file = config_file
        config_data = configobj.ConfigObj(config_file)
        self._config = config_data['server:main']

        self._args = []
        self.log_file = log_file or os.path.join(
            tempfile.gettempdir(), self.log_file_name)
        self.process = None
        self.server_out = None
        print("Using the {} configuration:{}".format(
            self.__class__.__name__, config_file))

        if not os.path.isfile(config_file):
            raise RuntimeError('Failed to get config at {}'.format(config_file))

    @property
    def command(self):
        return ' '.join(self._args)

    @property
    def http_url(self):
        template = 'http://{host}:{port}/'
        return template.format(**self._config)

    def host_url(self):
        return 'http://' + get_host_url(self.config_file)

    def get_rc_log(self):
        with open(self.log_file) as f:
            return f.read()

    def wait_until_ready(self, timeout=30):
        host = self._config['host']
        port = self._config['port']
        status_url = self.status_url_tmpl.format(host=host, port=port)
        start = time.time()

        while time.time() - start < timeout:
            try:
                urlopen(status_url)
                break
            except URLError:
                time.sleep(0.2)
        else:
            pytest.fail(
                "Starting the {} failed or took more than {} "
                "seconds. cmd: `{}`".format(
                    self.__class__.__name__, timeout, self.command))

        print('Server of {} ready at url {}'.format(
            self.__class__.__name__, status_url))

    def shutdown(self):
        self.process.kill()
        self.server_out.flush()
        self.server_out.close()

    def get_log_file_with_port(self):
        log_file = list(self.log_file.partition('.log'))
        log_file.insert(1, get_port(self.config_file))
        log_file = ''.join(log_file)
        return log_file


class RcVCSServer(ServerBase):
    """
    Represents a running VCSServer instance.
    """

    log_file_name = 'rc-vcsserver.log'
    status_url_tmpl = 'http://{host}:{port}/status'

    def __init__(self, config_file, log_file=None):
        super(RcVCSServer, self).__init__(config_file, log_file)
        self._args = [
            'gunicorn', '--paste', self.config_file]

    def start(self):
        env = os.environ.copy()

        self.log_file = self.get_log_file_with_port()
        self.server_out = open(self.log_file, 'w')

        host_url = self.host_url()
        assert_no_running_instance(host_url)

        print('rhodecode-vcsserver starting at: {}'.format(host_url))
        print('rhodecode-vcsserver command: {}'.format(self.command))
        print('rhodecode-vcsserver logfile: {}'.format(self.log_file))

        self.process = subprocess32.Popen(
            self._args, bufsize=0, env=env,
            stdout=self.server_out, stderr=self.server_out)


class RcWebServer(ServerBase):
    """
    Represents a running RCE web server used as a test fixture.
    """

    log_file_name = 'rc-web.log'
    status_url_tmpl = 'http://{host}:{port}/_admin/ops/ping'

    def __init__(self, config_file, log_file=None):
        super(RcWebServer, self).__init__(config_file, log_file)
        self._args = [
            'gunicorn', '--worker-class', 'gevent', '--paste', config_file]

    def start(self):
        env = os.environ.copy()
        env['RC_NO_TMP_PATH'] = '1'

        self.log_file = self.get_log_file_with_port()
        self.server_out = open(self.log_file, 'w')

        host_url = self.host_url()
        assert_no_running_instance(host_url)

        print('rhodecode-web starting at: {}'.format(host_url))
        print('rhodecode-web command: {}'.format(self.command))
        print('rhodecode-web logfile: {}'.format(self.log_file))

        self.process = subprocess32.Popen(
            self._args, bufsize=0, env=env,
            stdout=self.server_out, stderr=self.server_out)

    def repo_clone_url(self, repo_name, **kwargs):
        params = {
            'user': TEST_USER_ADMIN_LOGIN,
            'passwd': TEST_USER_ADMIN_PASS,
            'host': get_host_url(self.config_file),
            'cloned_repo': repo_name,
        }
        params.update(**kwargs)
        _url = 'http://%(user)s:%(passwd)s@%(host)s/%(cloned_repo)s' % params
        return _url
