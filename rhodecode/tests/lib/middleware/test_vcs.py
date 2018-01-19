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

from mock import patch, Mock

import rhodecode
from rhodecode.lib.middleware import vcs
from rhodecode.lib.middleware.simplesvn import (
    SimpleSvn, DisabledSimpleSvnApp, SimpleSvnApp)
from rhodecode.tests import SVN_REPO

svn_repo_path = '/'+ SVN_REPO

def test_is_hg():
    environ = {
        'PATH_INFO': svn_repo_path,
        'QUERY_STRING': 'cmd=changegroup',
        'HTTP_ACCEPT': 'application/mercurial'
    }
    assert vcs.is_hg(environ)


def test_is_hg_no_cmd():
    environ = {
        'PATH_INFO': svn_repo_path,
        'QUERY_STRING': '',
        'HTTP_ACCEPT': 'application/mercurial'
    }
    assert not vcs.is_hg(environ)


def test_is_hg_empty_cmd():
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': svn_repo_path,
        'QUERY_STRING': 'cmd=',
        'HTTP_ACCEPT': 'application/mercurial'
    }
    assert not vcs.is_hg(environ)


def test_is_svn_returns_true_if_subversion_is_in_a_dav_header():
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': svn_repo_path,
        'HTTP_DAV': 'http://subversion.tigris.org/xmlns/dav/svn/log-revprops'
    }
    assert vcs.is_svn(environ) is True


def test_is_svn_returns_false_if_subversion_is_not_in_a_dav_header():
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': svn_repo_path,
        'HTTP_DAV': 'http://stuff.tigris.org/xmlns/dav/svn/log-revprops'
    }
    assert vcs.is_svn(environ) is False


def test_is_svn_returns_false_if_no_dav_header():
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': svn_repo_path,
    }
    assert vcs.is_svn(environ) is False


def test_is_svn_returns_true_if_magic_path_segment():
    environ = {
        'PATH_INFO': '/stub-repository/!svn/rev/4',
    }
    assert vcs.is_svn(environ)


def test_is_svn_returns_true_if_propfind():
    environ = {
        'REQUEST_METHOD': 'PROPFIND',
        'PATH_INFO': svn_repo_path,
    }
    assert vcs.is_svn(environ) is True


def test_is_svn_allows_to_configure_the_magic_path(monkeypatch):
    """
    This is intended as a fallback in case someone has configured his
    Subversion server with a different magic path segment.
    """
    monkeypatch.setitem(
        rhodecode.CONFIG, 'rhodecode_subversion_magic_path', '/!my-magic')
    environ = {
        'REQUEST_METHOD': 'POST',
        'PATH_INFO': '/stub-repository/!my-magic/rev/4',
    }
    assert vcs.is_svn(environ)


class TestVCSMiddleware(object):
    def test_get_handler_app_retuns_svn_app_when_proxy_enabled(self, app):
        environ = {
            'PATH_INFO': SVN_REPO,
            'HTTP_DAV': 'http://subversion.tigris.org/xmlns/dav/svn/log'
        }
        application = Mock()
        config = {'appenlight': False, 'vcs.backends': ['svn']}
        registry = Mock()
        middleware = vcs.VCSMiddleware(
            application, registry, config, appenlight_client=None)
        middleware.use_gzip = False

        with patch.object(SimpleSvn, '_is_svn_enabled') as mock_method:
            mock_method.return_value = True
            application = middleware._get_handler_app(environ)
            assert isinstance(application, SimpleSvn)
            assert isinstance(application._create_wsgi_app(
                Mock(), Mock(), Mock()), SimpleSvnApp)

    def test_get_handler_app_retuns_dummy_svn_app_when_proxy_disabled(self, app):
        environ = {
            'PATH_INFO': SVN_REPO,
            'HTTP_DAV': 'http://subversion.tigris.org/xmlns/dav/svn/log'
        }
        application = Mock()
        config = {'appenlight': False, 'vcs.backends': ['svn']}
        registry = Mock()
        middleware = vcs.VCSMiddleware(
            application, registry, config, appenlight_client=None)
        middleware.use_gzip = False

        with patch.object(SimpleSvn, '_is_svn_enabled') as mock_method:
            mock_method.return_value = False
            application = middleware._get_handler_app(environ)
            assert isinstance(application, SimpleSvn)
            assert isinstance(application._create_wsgi_app(
                Mock(), Mock(), Mock()), DisabledSimpleSvnApp)
