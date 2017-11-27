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

import gzip
import shutil
import logging
import tempfile
import urlparse

from webob.exc import HTTPNotFound

import rhodecode
from rhodecode.lib.middleware.appenlight import wrap_in_appenlight_if_enabled
from rhodecode.lib.middleware.simplegit import SimpleGit, GIT_PROTO_PAT
from rhodecode.lib.middleware.simplehg import SimpleHg
from rhodecode.lib.middleware.simplesvn import SimpleSvn
from rhodecode.model.settings import VcsSettingsModel

log = logging.getLogger(__name__)

VCS_TYPE_KEY = '_rc_vcs_type'
VCS_TYPE_SKIP = '_rc_vcs_skip'


def is_git(environ):
    """
    Returns True if requests should be handled by GIT wsgi middleware
    """
    is_git_path = GIT_PROTO_PAT.match(environ['PATH_INFO'])
    log.debug(
        'request path: `%s` detected as GIT PROTOCOL %s', environ['PATH_INFO'],
        is_git_path is not None)

    return is_git_path


def is_hg(environ):
    """
    Returns True if requests target is mercurial server - header
    ``HTTP_ACCEPT`` of such request would start with ``application/mercurial``.
    """
    is_hg_path = False

    http_accept = environ.get('HTTP_ACCEPT')

    if http_accept and http_accept.startswith('application/mercurial'):
        query = urlparse.parse_qs(environ['QUERY_STRING'])
        if 'cmd' in query:
            is_hg_path = True

    log.debug(
        'request path: `%s` detected as HG PROTOCOL %s', environ['PATH_INFO'],
        is_hg_path)

    return is_hg_path


def is_svn(environ):
    """
    Returns True if requests target is Subversion server
    """

    http_dav = environ.get('HTTP_DAV', '')
    magic_path_segment = rhodecode.CONFIG.get(
        'rhodecode_subversion_magic_path', '/!svn')
    is_svn_path = (
        'subversion' in http_dav or
        magic_path_segment in environ['PATH_INFO']
        or environ['REQUEST_METHOD'] in ['PROPFIND', 'PROPPATCH']
    )
    log.debug(
        'request path: `%s` detected as SVN PROTOCOL %s', environ['PATH_INFO'],
        is_svn_path)

    return is_svn_path


class GunzipMiddleware(object):
    """
    WSGI middleware that unzips gzip-encoded requests before
    passing on to the underlying application.
    """

    def __init__(self, application):
        self.app = application

    def __call__(self, environ, start_response):
        accepts_encoding_header = environ.get('HTTP_CONTENT_ENCODING', b'')

        if b'gzip' in accepts_encoding_header:
            log.debug('gzip detected, now running gunzip wrapper')
            wsgi_input = environ['wsgi.input']

            if not hasattr(environ['wsgi.input'], 'seek'):
                # The gzip implementation in the standard library of Python 2.x
                # requires the '.seek()' and '.tell()' methods to be available
                # on the input stream.  Read the data into a temporary file to
                # work around this limitation.

                wsgi_input = tempfile.SpooledTemporaryFile(64 * 1024 * 1024)
                shutil.copyfileobj(environ['wsgi.input'], wsgi_input)
                wsgi_input.seek(0)

            environ['wsgi.input'] = gzip.GzipFile(fileobj=wsgi_input, mode='r')
            # since we "Ungzipped" the content we say now it's no longer gzip
            # content encoding
            del environ['HTTP_CONTENT_ENCODING']

            # content length has changes ? or i'm not sure
            if 'CONTENT_LENGTH' in environ:
                del environ['CONTENT_LENGTH']
        else:
            log.debug('content not gzipped, gzipMiddleware passing '
                      'request further')
        return self.app(environ, start_response)


def is_vcs_call(environ):
    if VCS_TYPE_KEY in environ:
        raw_type = environ[VCS_TYPE_KEY]
        return raw_type and raw_type != VCS_TYPE_SKIP
    return False


def detect_vcs_request(environ, backends):
    checks = {
        'hg': (is_hg, SimpleHg),
        'git': (is_git, SimpleGit),
        'svn': (is_svn, SimpleSvn),
    }
    handler = None

    if VCS_TYPE_KEY in environ:
        raw_type = environ[VCS_TYPE_KEY]
        if raw_type == VCS_TYPE_SKIP:
            log.debug('got `skip` marker for vcs detection, skipping...')
            return handler

        _check, handler = checks.get(raw_type) or [None, None]
        if handler:
            log.debug('got handler:%s from environ', handler)

    if not handler:
        log.debug('checking if request is of VCS type in order: %s', backends)
        for vcs_type in backends:
            vcs_check, _handler = checks[vcs_type]
            if vcs_check(environ):
                log.debug('vcs handler found %s', _handler)
                handler = _handler
                break

    return handler


class VCSMiddleware(object):

    def __init__(self, app, registry, config, appenlight_client):
        self.application = app
        self.registry = registry
        self.config = config
        self.appenlight_client = appenlight_client
        self.use_gzip = True
        # order in which we check the middlewares, based on vcs.backends config
        self.check_middlewares = config['vcs.backends']

    def vcs_config(self, repo_name=None):
        """
        returns serialized VcsSettings
        """
        try:
            return VcsSettingsModel(
                repo=repo_name).get_ui_settings_as_config_obj()
        except Exception:
            pass

    def wrap_in_gzip_if_enabled(self, app, config):
        if self.use_gzip:
            app = GunzipMiddleware(app)
        return app

    def _get_handler_app(self, environ):
        app = None
        log.debug('VCSMiddleware: detecting vcs type.')
        handler = detect_vcs_request(environ, self.check_middlewares)
        if handler:
            app = handler(self.config, self.registry)

        return app

    def __call__(self, environ, start_response):
        # check if we handle one of interesting protocols, optionally extract
        # specific vcsSettings and allow changes of how things are wrapped
        vcs_handler = self._get_handler_app(environ)
        if vcs_handler:
            # translate the _REPO_ID into real repo NAME for usage
            # in middleware
            environ['PATH_INFO'] = vcs_handler._get_by_id(environ['PATH_INFO'])

            # Set acl, url and vcs repo names.
            vcs_handler.set_repo_names(environ)

            # register repo config back to the handler
            vcs_conf = self.vcs_config(vcs_handler.acl_repo_name)
            # maybe damaged/non existent settings. We still want to
            # pass that point to validate on is_valid_and_existing_repo
            # and return proper HTTP Code back to client
            if vcs_conf:
                vcs_handler.repo_vcs_config = vcs_conf

            # check for type, presence in database and on filesystem
            if not vcs_handler.is_valid_and_existing_repo(
                    vcs_handler.acl_repo_name,
                    vcs_handler.base_path,
                    vcs_handler.SCM):
                return HTTPNotFound()(environ, start_response)

            environ['REPO_NAME'] = vcs_handler.url_repo_name

            # Wrap handler in middlewares if they are enabled.
            vcs_handler = self.wrap_in_gzip_if_enabled(
                vcs_handler, self.config)
            vcs_handler, _ = wrap_in_appenlight_if_enabled(
                vcs_handler, self.config, self.appenlight_client)

            return vcs_handler(environ, start_response)

        return self.application(environ, start_response)
