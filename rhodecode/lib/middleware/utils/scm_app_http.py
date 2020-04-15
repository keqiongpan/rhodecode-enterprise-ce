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
Implementation of the scm_app interface using raw HTTP communication.
"""

import base64
import logging
import urlparse
import wsgiref.util

import msgpack
import requests
import webob.request

import rhodecode


log = logging.getLogger(__name__)


def create_git_wsgi_app(repo_path, repo_name, config):
    url = _vcs_streaming_url() + 'git/'
    return VcsHttpProxy(url, repo_path, repo_name, config)


def create_hg_wsgi_app(repo_path, repo_name, config):
    url = _vcs_streaming_url() + 'hg/'
    return VcsHttpProxy(url, repo_path, repo_name, config)


def _vcs_streaming_url():
    template = 'http://{}/stream/'
    return template.format(rhodecode.CONFIG['vcs.server'])


# TODO: johbo: Avoid the global.
session = requests.Session()
# Requests speedup, avoid reading .netrc and similar
session.trust_env = False

# prevent urllib3 spawning our logs.
logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(
    logging.WARNING)


class VcsHttpProxy(object):
    """
    A WSGI application which proxies vcs requests.

    The goal is to shuffle the data around without touching it. The only
    exception is the extra data from the config object which we send to the
    server as well.
    """

    def __init__(self, url, repo_path, repo_name, config):
        """
        :param str url: The URL of the VCSServer to call.
        """
        self._url = url
        self._repo_name = repo_name
        self._repo_path = repo_path
        self._config = config
        log.debug(
            "Creating VcsHttpProxy for repo %s, url %s",
            repo_name, url)

    def __call__(self, environ, start_response):
        config = msgpack.packb(self._config)
        request = webob.request.Request(environ)
        request_headers = request.headers
        request_headers.update({
            # TODO: johbo: Remove this, rely on URL path only
            'X-RC-Repo-Name': self._repo_name,
            'X-RC-Repo-Path': self._repo_path,
            'X-RC-Path-Info': environ['PATH_INFO'],
            # TODO: johbo: Avoid encoding and put this into payload?
            'X-RC-Repo-Config': base64.b64encode(config),
            'X-RC-Locked-Status-Code': rhodecode.CONFIG.get('lock_ret_code')
        })

        method = environ['REQUEST_METHOD']

        # Preserve the query string
        url = self._url
        url = urlparse.urljoin(url, self._repo_name)
        if environ.get('QUERY_STRING'):
            url += '?' + environ['QUERY_STRING']

        log.debug('http-app: preparing request to: %s', url)
        response = session.request(
            method,
            url,
            data=_maybe_stream_request(environ),
            headers=request_headers,
            stream=True)

        log.debug('http-app: got vcsserver response: %s', response)
        if response.status_code >= 500:
            log.error('Exception returned by vcsserver at: %s %s, %s',
                      url, response.status_code, response.content)

        # Preserve the headers of the response, except hop_by_hop ones
        response_headers = [
            (h, v) for h, v in response.headers.items()
            if not wsgiref.util.is_hop_by_hop(h)
        ]

        # Build status argument for start_response callable.
        status = '{status_code} {reason_phrase}'.format(
            status_code=response.status_code,
            reason_phrase=response.reason)

        start_response(status, response_headers)
        return _maybe_stream_response(response)


def read_in_chunks(stream_obj, block_size=1024, chunks=-1):
    """
    Read Stream in chunks, default chunk size: 1k.
    """
    while chunks:
        data = stream_obj.read(block_size)
        if not data:
            break
        yield data
        chunks -= 1


def _is_request_chunked(environ):
    stream = environ.get('HTTP_TRANSFER_ENCODING', '') == 'chunked'
    return stream


def _maybe_stream_request(environ):
    path = environ['PATH_INFO']
    stream = _is_request_chunked(environ)
    log.debug('handling request `%s` with stream support: %s', path, stream)

    if stream:
        # set stream by 256k
        return read_in_chunks(environ['wsgi.input'], block_size=1024 * 256)
    else:
        return environ['wsgi.input'].read()


def _maybe_stream_response(response):
    """
    Try to generate chunks from the response if it is chunked.
    """
    stream = _is_chunked(response)
    log.debug('returning response with stream: %s', stream)
    if stream:
        # read in 256k Chunks
        return response.raw.read_chunked(amt=1024 * 256)
    else:
        return [response.content]


def _is_chunked(response):
    return response.headers.get('Transfer-Encoding', '') == 'chunked'
