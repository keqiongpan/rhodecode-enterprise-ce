# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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

import base64
import logging
import urllib
from urlparse import urljoin

import requests
from pyramid.httpexceptions import HTTPNotAcceptable

from rhodecode.lib import rc_cache
from rhodecode.lib.middleware import simplevcs
from rhodecode.lib.utils import is_valid_repo
from rhodecode.lib.utils2 import str2bool, safe_int
from rhodecode.lib.ext_json import json
from rhodecode.lib.hooks_daemon import store_txn_id_data


log = logging.getLogger(__name__)


class SimpleSvnApp(object):
    IGNORED_HEADERS = [
        'connection', 'keep-alive', 'content-encoding',
        'transfer-encoding', 'content-length']
    rc_extras = {}

    def __init__(self, config):
        self.config = config

    def __call__(self, environ, start_response):
        request_headers = self._get_request_headers(environ)

        data = environ['wsgi.input']
        # johbo: Avoid that we end up with sending the request in chunked
        # transfer encoding (mainly on Gunicorn). If we know the content
        # length, then we should transfer the payload in one request.
        if environ['REQUEST_METHOD'] == 'MKCOL' or 'CONTENT_LENGTH' in environ:
            data = data.read()
            if data.startswith('(create-txn-with-props'):
                # store on-the-fly our rc_extra using svn revision properties
                # those can be read later on in hooks executed so we have a way
                # to pass in the data into svn hooks
                rc_data = base64.urlsafe_b64encode(json.dumps(self.rc_extras))
                rc_data_len = len(rc_data)
                # header defines data lenght, and serialized data
                skel = ' rc-scm-extras {} {}'.format(rc_data_len, rc_data)
                data = data[:-2] + skel + '))'

        log.debug('Calling: %s method via `%s`', environ['REQUEST_METHOD'],
                  self._get_url(environ['PATH_INFO']))

        response = requests.request(
            environ['REQUEST_METHOD'], self._get_url(environ['PATH_INFO']),
            data=data, headers=request_headers)

        if response.status_code not in [200, 401]:
            if response.status_code >= 500:
                log.error('Got SVN response:%s with text:\n`%s`',
                          response, response.text)
            else:
                log.debug('Got SVN response:%s with text:\n`%s`',
                          response, response.text)
        else:
            log.debug('got response code: %s', response.status_code)

        response_headers = self._get_response_headers(response.headers)

        if response.headers.get('SVN-Txn-name'):
            svn_tx_id = response.headers.get('SVN-Txn-name')
            txn_id = rc_cache.utils.compute_key_from_params(
                self.config['repository'], svn_tx_id)
            port = safe_int(self.rc_extras['hooks_uri'].split(':')[-1])
            store_txn_id_data(txn_id, {'port': port})

        start_response(
            '{} {}'.format(response.status_code, response.reason),
            response_headers)
        return response.iter_content(chunk_size=1024)

    def _get_url(self, path):
        url_path = urljoin(
            self.config.get('subversion_http_server_url', ''), path)
        url_path = urllib.quote(url_path, safe="/:=~+!$,;'")
        return url_path

    def _get_request_headers(self, environ):
        headers = {}

        for key in environ:
            if not key.startswith('HTTP_'):
                continue
            new_key = key.split('_')
            new_key = [k.capitalize() for k in new_key[1:]]
            new_key = '-'.join(new_key)
            headers[new_key] = environ[key]

        if 'CONTENT_TYPE' in environ:
            headers['Content-Type'] = environ['CONTENT_TYPE']

        if 'CONTENT_LENGTH' in environ:
            headers['Content-Length'] = environ['CONTENT_LENGTH']

        return headers

    def _get_response_headers(self, headers):
        headers = [
            (h, headers[h])
            for h in headers
            if h.lower() not in self.IGNORED_HEADERS
        ]

        return headers


class DisabledSimpleSvnApp(object):
    def __init__(self, config):
        self.config = config

    def __call__(self, environ, start_response):
        reason = 'Cannot handle SVN call because: SVN HTTP Proxy is not enabled'
        log.warning(reason)
        return HTTPNotAcceptable(reason)(environ, start_response)


class SimpleSvn(simplevcs.SimpleVCS):

    SCM = 'svn'
    READ_ONLY_COMMANDS = ('OPTIONS', 'PROPFIND', 'GET', 'REPORT')
    DEFAULT_HTTP_SERVER = 'http://localhost:8090'

    def _get_repository_name(self, environ):
        """
        Gets repository name out of PATH_INFO header

        :param environ: environ where PATH_INFO is stored
        """
        path = environ['PATH_INFO'].split('!')
        repo_name = path[0].strip('/')

        # SVN includes the whole path in it's requests, including
        # subdirectories inside the repo. Therefore we have to search for
        # the repo root directory.
        if not is_valid_repo(
                repo_name, self.base_path, explicit_scm=self.SCM):
            current_path = ''
            for component in repo_name.split('/'):
                current_path += component
                if is_valid_repo(
                        current_path, self.base_path, explicit_scm=self.SCM):
                    return current_path
                current_path += '/'

        return repo_name

    def _get_action(self, environ):
        return (
            'pull'
            if environ['REQUEST_METHOD'] in self.READ_ONLY_COMMANDS
            else 'push')

    def _should_use_callback_daemon(self, extras, environ, action):
        # only MERGE command triggers hooks, so we don't want to start
        # hooks server too many times. POST however starts the svn transaction
        # so we also need to run the init of callback daemon of POST
        if environ['REQUEST_METHOD'] in ['MERGE', 'POST']:
            return True
        return False

    def _create_wsgi_app(self, repo_path, repo_name, config):
        if self._is_svn_enabled():
            return SimpleSvnApp(config)
        # we don't have http proxy enabled return dummy request handler
        return DisabledSimpleSvnApp(config)

    def _is_svn_enabled(self):
        conf = self.repo_vcs_config
        return str2bool(conf.get('vcs_svn_proxy', 'http_requests_enabled'))

    def _create_config(self, extras, repo_name):
        conf = self.repo_vcs_config
        server_url = conf.get('vcs_svn_proxy', 'http_server_url')
        server_url = server_url or self.DEFAULT_HTTP_SERVER

        extras['subversion_http_server_url'] = server_url
        return extras
