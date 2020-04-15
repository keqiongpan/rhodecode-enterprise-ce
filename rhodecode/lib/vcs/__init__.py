# -*- coding: utf-8 -*-

# Copyright (C) 2014-2020 RhodeCode GmbH
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
Various version Control System version lib (vcs) management abstraction layer
for Python. Build with server client architecture.
"""
import atexit
import logging
import urlparse
from cStringIO import StringIO

import rhodecode
from rhodecode.lib.vcs.conf import settings
from rhodecode.lib.vcs.backends import get_vcs_instance, get_backend
from rhodecode.lib.vcs.exceptions import (
    VCSError, RepositoryError, CommitError, VCSCommunicationError)

VERSION = (0, 5, 0, 'dev')

__version__ = '.'.join((str(each) for each in VERSION[:4]))

__all__ = [
    'get_version', 'get_vcs_instance', 'get_backend',
    'VCSError', 'RepositoryError', 'CommitError', 'VCSCommunicationError'
]

log = logging.getLogger(__name__)

# The pycurl library directly accesses C API functions and is not patched by
# gevent. This will potentially lead to deadlocks due to incompatibility to
# gevent. Therefore we check if gevent is active and import a gevent compatible
# wrapper in that case.
try:
    from gevent import monkey
    if monkey.is_module_patched('__builtin__'):
        import geventcurl as pycurl
        log.debug('Using gevent comapatible pycurl: %s', pycurl)
    else:
        import pycurl
except ImportError:
    import pycurl


def get_version():
    """
    Returns shorter version (digit parts only) as string.
    """
    return '.'.join((str(each) for each in VERSION[:3]))


def connect_http(server_and_port):
    from rhodecode.lib.vcs import connection, client_http
    from rhodecode.lib.middleware.utils import scm_app

    session_factory = client_http.ThreadlocalSessionFactory()

    connection.Git = client_http.RemoteVCSMaker(
        server_and_port, '/git', 'git', session_factory)
    connection.Hg = client_http.RemoteVCSMaker(
        server_and_port, '/hg', 'hg', session_factory)
    connection.Svn = client_http.RemoteVCSMaker(
        server_and_port, '/svn', 'svn', session_factory)
    connection.Service = client_http.ServiceConnection(
        server_and_port, '/_service', session_factory)

    scm_app.HG_REMOTE_WSGI = client_http.VcsHttpProxy(
        server_and_port, '/proxy/hg')
    scm_app.GIT_REMOTE_WSGI = client_http.VcsHttpProxy(
        server_and_port, '/proxy/git')

    @atexit.register
    def free_connection_resources():
        connection.Git = None
        connection.Hg = None
        connection.Svn = None
        connection.Service = None


def connect_vcs(server_and_port, protocol):
    """
    Initializes the connection to the vcs server.

    :param server_and_port: str, e.g. "localhost:9900"
    :param protocol: str or "http"
    """
    if protocol == 'http':
        connect_http(server_and_port)
    else:
        raise Exception('Invalid vcs server protocol "{}"'.format(protocol))


class CurlSession(object):
    """
    Modeled so that it provides a subset of the requests interface.

    This has been created so that it does only provide a minimal API for our
    needs. The parts which it provides are based on the API of the library
    `requests` which allows us to easily benchmark against it.

    Please have a look at the class :class:`requests.Session` when you extend
    it.
    """

    def __init__(self):
        curl = pycurl.Curl()
        # TODO: johbo: I did test with 7.19 of libcurl. This version has
        # trouble with 100 - continue being set in the expect header. This
        # can lead to massive performance drops, switching it off here.
        curl.setopt(curl.HTTPHEADER, ["Expect:"])
        curl.setopt(curl.TCP_NODELAY, True)
        curl.setopt(curl.PROTOCOLS, curl.PROTO_HTTP)
        curl.setopt(curl.USERAGENT, 'RhodeCode HTTP {}'.format(rhodecode.__version__))
        curl.setopt(curl.SSL_VERIFYPEER, 0)
        curl.setopt(curl.SSL_VERIFYHOST, 0)
        self._curl = curl

    def post(self, url, data, allow_redirects=False):
        response_buffer = StringIO()

        curl = self._curl
        curl.setopt(curl.URL, url)
        curl.setopt(curl.POST, True)
        curl.setopt(curl.POSTFIELDS, data)
        curl.setopt(curl.FOLLOWLOCATION, allow_redirects)
        curl.setopt(curl.WRITEDATA, response_buffer)
        curl.perform()

        status_code = curl.getinfo(pycurl.HTTP_CODE)

        return CurlResponse(response_buffer, status_code)


class CurlResponse(object):
    """
    The response of a request, modeled after the requests API.

    This class provides a subset of the response interface known from the
    library `requests`. It is intentionally kept similar, so that we can use
    `requests` as a drop in replacement for benchmarking purposes.
    """

    def __init__(self, response_buffer, status_code):
        self._response_buffer = response_buffer
        self._status_code = status_code

    @property
    def content(self):
        try:
            return self._response_buffer.getvalue()
        finally:
            self._response_buffer.close()

    @property
    def status_code(self):
        return self._status_code

    def iter_content(self, chunk_size):
        self._response_buffer.seek(0)
        while 1:
            chunk = self._response_buffer.read(chunk_size)
            if not chunk:
                break
            yield chunk


def _create_http_rpc_session():
    session = CurlSession()
    return session
