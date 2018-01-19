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

import pytest
import urlparse
import mock
import simplejson as json

from rhodecode.lib.vcs.backends.base import Config
from rhodecode.tests.lib.middleware import mock_scm_app
import rhodecode.lib.middleware.simplegit as simplegit


def get_environ(url, request_method):
    """Construct a minimum WSGI environ based on the URL."""
    parsed_url = urlparse.urlparse(url)
    environ = {
        'PATH_INFO': parsed_url.path,
        'QUERY_STRING': parsed_url.query,
        'REQUEST_METHOD': request_method,
    }

    return environ


@pytest.mark.parametrize(
    'url, expected_action, request_method',
    [
        ('/foo/bar/info/refs?service=git-upload-pack', 'pull', 'GET'),
        ('/foo/bar/info/refs?service=git-receive-pack', 'push', 'GET'),
        ('/foo/bar/git-upload-pack', 'pull', 'GET'),
        ('/foo/bar/git-receive-pack', 'push', 'GET'),
        # Edge case: missing data for info/refs
        ('/foo/info/refs?service=', 'pull', 'GET'),
        ('/foo/info/refs', 'pull', 'GET'),
        # Edge case: git command comes with service argument
        ('/foo/git-upload-pack?service=git-receive-pack', 'pull', 'GET'),
        ('/foo/git-receive-pack?service=git-upload-pack', 'push', 'GET'),
        # Edge case: repo name conflicts with git commands
        ('/git-receive-pack/git-upload-pack', 'pull', 'GET'),
        ('/git-receive-pack/git-receive-pack', 'push', 'GET'),
        ('/git-upload-pack/git-upload-pack', 'pull', 'GET'),
        ('/git-upload-pack/git-receive-pack', 'push', 'GET'),
        ('/foo/git-receive-pack', 'push', 'GET'),
        # Edge case: not a smart protocol url
        ('/foo/bar', 'pull', 'GET'),
        # GIT LFS cases, batch
        ('/foo/bar/info/lfs/objects/batch', 'push', 'GET'),
        ('/foo/bar/info/lfs/objects/batch', 'pull', 'POST'),
        # GIT LFS oid, dl/upl
        ('/foo/bar/info/lfs/abcdeabcde', 'pull', 'GET'),
        ('/foo/bar/info/lfs/abcdeabcde', 'push', 'PUT'),
        ('/foo/bar/info/lfs/abcdeabcde', 'push', 'POST'),
        # Edge case: repo name conflicts with git commands
        ('/info/lfs/info/lfs/objects/batch', 'push', 'GET'),
        ('/info/lfs/info/lfs/objects/batch', 'pull', 'POST'),

    ])
def test_get_action(url, expected_action, request_method, baseapp, request_stub):
    app = simplegit.SimpleGit(config={'auth_ret_code': '', 'base_path': ''},
                              registry=request_stub.registry)
    assert expected_action == app._get_action(get_environ(url, request_method))


@pytest.mark.parametrize(
    'url, expected_repo_name, request_method',
    [
        ('/foo/info/refs?service=git-upload-pack', 'foo', 'GET'),
        ('/foo/bar/info/refs?service=git-receive-pack', 'foo/bar', 'GET'),
        ('/foo/git-upload-pack', 'foo', 'GET'),
        ('/foo/git-receive-pack', 'foo', 'GET'),
        ('/foo/bar/git-upload-pack', 'foo/bar', 'GET'),
        ('/foo/bar/git-receive-pack', 'foo/bar', 'GET'),

        # GIT LFS cases, batch
        ('/foo/bar/info/lfs/objects/batch', 'foo/bar', 'GET'),
        ('/example-git/info/lfs/objects/batch', 'example-git', 'POST'),
        # GIT LFS oid, dl/upl
        ('/foo/info/lfs/abcdeabcde', 'foo', 'GET'),
        ('/foo/bar/info/lfs/abcdeabcde', 'foo/bar', 'PUT'),
        ('/my-git-repo/info/lfs/abcdeabcde', 'my-git-repo', 'POST'),
        # Edge case: repo name conflicts with git commands
        ('/info/lfs/info/lfs/objects/batch', 'info/lfs', 'GET'),
        ('/info/lfs/info/lfs/objects/batch', 'info/lfs', 'POST'),

    ])
def test_get_repository_name(url, expected_repo_name, request_method, baseapp, request_stub):
    app = simplegit.SimpleGit(config={'auth_ret_code': '', 'base_path': ''},
                              registry=request_stub.registry)
    assert expected_repo_name == app._get_repository_name(
        get_environ(url, request_method))


def test_get_config(user_util, baseapp, request_stub):
    repo = user_util.create_repo(repo_type='git')
    app = simplegit.SimpleGit(config={'auth_ret_code': '', 'base_path': ''},
                              registry=request_stub.registry)
    extras = {'foo': 'FOO', 'bar': 'BAR'}

    # We copy the extras as the method below will change the contents.
    git_config = app._create_config(dict(extras), repo_name=repo.repo_name)

    expected_config = dict(extras)
    expected_config.update({
        'git_update_server_info': False,
        'git_lfs_enabled': False,
        'git_lfs_store_path': git_config['git_lfs_store_path']
    })

    assert git_config == expected_config


def test_create_wsgi_app_uses_scm_app_from_simplevcs(baseapp, request_stub):
    config = {
        'auth_ret_code': '',
        'base_path': '',
        'vcs.scm_app_implementation':
            'rhodecode.tests.lib.middleware.mock_scm_app',
    }
    app = simplegit.SimpleGit(config=config, registry=request_stub.registry)
    wsgi_app = app._create_wsgi_app('/tmp/test', 'test_repo', {})
    assert wsgi_app is mock_scm_app.mock_git_wsgi
