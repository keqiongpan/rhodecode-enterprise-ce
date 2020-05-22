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

import urlparse

import mock
import pytest
import simplejson as json

from rhodecode.lib.vcs.backends.base import Config
from rhodecode.tests.lib.middleware import mock_scm_app
import rhodecode.lib.middleware.simplehg as simplehg


def get_environ(url):
    """Construct a minimum WSGI environ based on the URL."""
    parsed_url = urlparse.urlparse(url)
    environ = {
        'PATH_INFO': parsed_url.path,
        'QUERY_STRING': parsed_url.query,
    }

    return environ


@pytest.mark.parametrize(
    'url, expected_action',
    [
        ('/foo/bar?cmd=unbundle&key=tip', 'push'),
        ('/foo/bar?cmd=pushkey&key=tip', 'push'),
        ('/foo/bar?cmd=listkeys&key=tip', 'pull'),
        ('/foo/bar?cmd=changegroup&key=tip', 'pull'),
        ('/foo/bar?cmd=hello', 'pull'),
        ('/foo/bar?cmd=batch', 'push'),
        ('/foo/bar?cmd=putlfile', 'push'),
        # Edge case: unknown argument: assume push
        ('/foo/bar?cmd=unknown&key=tip', 'push'),
        ('/foo/bar?cmd=&key=tip', 'push'),
        # Edge case: not cmd argument
        ('/foo/bar?key=tip', 'push'),
    ])
def test_get_action(url, expected_action, request_stub):
    app = simplehg.SimpleHg(config={'auth_ret_code': '', 'base_path': ''},
                            registry=request_stub.registry)
    assert expected_action == app._get_action(get_environ(url))


@pytest.mark.parametrize(
    'environ, expected_xargs, expected_batch',
    [
        ({},
         [''], ['push']),

        ({'HTTP_X_HGARG_1': ''},
         [''], ['push']),

        ({'HTTP_X_HGARG_1': 'cmds=listkeys+namespace%3Dphases'},
         ['listkeys namespace=phases'], ['pull']),

        ({'HTTP_X_HGARG_1': 'cmds=pushkey+namespace%3Dbookmarks%2Ckey%3Dbm%2Cold%3D%2Cnew%3Dcb9a9f314b8b07ba71012fcdbc544b5a4d82ff5b'},
         ['pushkey namespace=bookmarks,key=bm,old=,new=cb9a9f314b8b07ba71012fcdbc544b5a4d82ff5b'], ['push']),

        ({'HTTP_X_HGARG_1': 'namespace=phases'},
         ['namespace=phases'], ['push']),

    ])
def test_xarg_and_batch_commands(environ, expected_xargs, expected_batch):
    app = simplehg.SimpleHg

    result = app._get_xarg_headers(environ)
    result_batch = app._get_batch_cmd(environ)
    assert expected_xargs == result
    assert expected_batch == result_batch


@pytest.mark.parametrize(
    'url, expected_repo_name',
    [
        ('/foo?cmd=unbundle&key=tip', 'foo'),
        ('/foo/bar?cmd=pushkey&key=tip', 'foo/bar'),
        ('/foo/bar/baz?cmd=listkeys&key=tip', 'foo/bar/baz'),
        # Repos with trailing slashes.
        ('/foo/?cmd=unbundle&key=tip', 'foo'),
        ('/foo/bar/?cmd=pushkey&key=tip', 'foo/bar'),
        ('/foo/bar/baz/?cmd=listkeys&key=tip', 'foo/bar/baz'),
    ])
def test_get_repository_name(url, expected_repo_name, request_stub):
    app = simplehg.SimpleHg(config={'auth_ret_code': '', 'base_path': ''},
                            registry=request_stub.registry)
    assert expected_repo_name == app._get_repository_name(get_environ(url))


def test_get_config(user_util, baseapp, request_stub):
    repo = user_util.create_repo(repo_type='git')
    app = simplehg.SimpleHg(config={'auth_ret_code': '', 'base_path': ''},
                            registry=request_stub.registry)
    extras = [('foo', 'FOO', 'bar', 'BAR')]

    hg_config = app._create_config(extras, repo_name=repo.repo_name)

    config = simplehg.utils.make_db_config(repo=repo.repo_name)
    config.set('rhodecode', 'RC_SCM_DATA', json.dumps(extras))
    hg_config_org = config

    expected_config = [
        ('vcs_svn_tag', 'ff89f8c714d135d865f44b90e5413b88de19a55f', '/tags/*'),
        ('web', 'push_ssl', 'False'),
        ('web', 'allow_push', '*'),
        ('web', 'allow_archive', 'gz zip bz2'),
        ('web', 'baseurl', '/'),
        ('vcs_git_lfs', 'store_location', hg_config_org.get('vcs_git_lfs', 'store_location')),
        ('vcs_svn_branch', '9aac1a38c3b8a0cdc4ae0f960a5f83332bc4fa5e', '/branches/*'),
        ('vcs_svn_branch', 'c7e6a611c87da06529fd0dd733308481d67c71a8', '/trunk'),
        ('largefiles', 'usercache', hg_config_org.get('largefiles', 'usercache')),
        ('hooks', 'preoutgoing.pre_pull', 'python:vcsserver.hooks.pre_pull'),
        ('hooks', 'prechangegroup.pre_push', 'python:vcsserver.hooks.pre_push'),
        ('hooks', 'outgoing.pull_logger', 'python:vcsserver.hooks.log_pull_action'),
        ('hooks', 'pretxnchangegroup.pre_push', 'python:vcsserver.hooks.pre_push'),
        ('hooks', 'changegroup.push_logger', 'python:vcsserver.hooks.log_push_action'),
        ('hooks', 'changegroup.repo_size', 'python:vcsserver.hooks.repo_size'),
        ('phases', 'publish', 'True'),
        ('extensions', 'largefiles', ''),
        ('paths', '/', hg_config_org.get('paths', '/')),
        ('rhodecode', 'RC_SCM_DATA', '[["foo", "FOO", "bar", "BAR"]]')
    ]
    for entry in expected_config:
        assert entry in hg_config


def test_create_wsgi_app_uses_scm_app_from_simplevcs(request_stub):
    config = {
        'auth_ret_code': '',
        'base_path': '',
        'vcs.scm_app_implementation':
            'rhodecode.tests.lib.middleware.mock_scm_app',
    }
    app = simplehg.SimpleHg(config=config, registry=request_stub.registry)
    wsgi_app = app._create_wsgi_app('/tmp/test', 'test_repo', {})
    assert wsgi_app is mock_scm_app.mock_hg_wsgi
