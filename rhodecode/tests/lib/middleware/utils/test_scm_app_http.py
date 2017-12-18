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

import pytest

from rhodecode.tests.utils import CustomTestApp
from rhodecode.lib.middleware.utils import scm_app_http, scm_app
from rhodecode.lib.vcs.conf import settings


def vcs_http_app(vcsserver_http_echo_app):
    """
    VcsHttpProxy wrapped in WebTest.
    """
    git_url = vcsserver_http_echo_app.http_url + 'stream/git/'
    vcs_http_proxy = scm_app_http.VcsHttpProxy(
        git_url, 'stub_path', 'stub_name', None)
    app = CustomTestApp(vcs_http_proxy)
    return app


@pytest.fixture(scope='module')
def vcsserver_http_echo_app(request, vcsserver_factory):
    """
    A running VCSServer with the EchoApp activated via HTTP.
    """
    vcsserver = vcsserver_factory(
        request=request,
        overrides=[{'app:main': {'dev.use_echo_app': 'true'}}])
    return vcsserver


@pytest.fixture(scope='session')
def data():
    one_kb = "x" * 1024
    return one_kb * 1024 * 10


def test_reuse_app_no_data(repeat, vcsserver_http_echo_app):
    app = vcs_http_app(vcsserver_http_echo_app)
    for x in xrange(repeat / 10):
        response = app.post('/')
        assert response.status_code == 200


def test_reuse_app_with_data(data, repeat, vcsserver_http_echo_app):
    app = vcs_http_app(vcsserver_http_echo_app)
    for x in xrange(repeat / 10):
        response = app.post('/', params=data)
        assert response.status_code == 200


def test_create_app_per_request_no_data(repeat, vcsserver_http_echo_app):
    for x in xrange(repeat / 10):
        app = vcs_http_app(vcsserver_http_echo_app)
        response = app.post('/')
        assert response.status_code == 200


def test_create_app_per_request_with_data(
        data, repeat, vcsserver_http_echo_app):
    for x in xrange(repeat / 10):
        app = vcs_http_app(vcsserver_http_echo_app)
        response = app.post('/', params=data)
        assert response.status_code == 200
