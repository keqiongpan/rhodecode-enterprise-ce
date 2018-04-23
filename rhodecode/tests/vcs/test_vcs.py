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

"""
Tests for main module's methods.
"""
import os
import tempfile
import shutil
import mock
import pytest

from rhodecode.lib.vcs import VCSError, get_backend, get_vcs_instance


pytestmark = pytest.mark.usefixtures("baseapp")


def test_get_backend(backend):
    repo_class = get_backend(backend.alias)
    assert repo_class == backend.repo.scm_instance().__class__


def test_alias_detect(backend):
    alias = backend.alias
    path = backend.repo.scm_instance().path

    new_backend = get_backend(alias)
    repo = new_backend(path)

    assert alias == repo.alias


def test_wrong_alias():
    alias = 'wrong_alias'
    with pytest.raises(VCSError):
        get_backend(alias)


def test_get_vcs_instance_by_path(vcs_repo):
    repo = get_vcs_instance(vcs_repo.path)

    assert repo.__class__ == vcs_repo.__class__
    assert repo.path == vcs_repo.path
    assert repo.alias == vcs_repo.alias
    assert repo.name == vcs_repo.name


def test_get_vcs_instance_by_path_empty_dir(request, tmpdir):
    """
    Test that ``get_vcs_instance_by_path`` returns None if a path is passed
    to an empty directory.
    """
    empty_dir = str(tmpdir)
    repo = get_vcs_instance(empty_dir)
    assert repo is None


def test_get_vcs_instance_by_path_multiple_repos(request):
    """
    Test that ``get_vcs_instance_by_path`` returns None if a path is passed
    to a directory with multiple repositories.
    """
    empty_dir = tempfile.mkdtemp(prefix='pytest-empty-dir-')
    os.mkdir(os.path.join(empty_dir, '.git'))
    os.mkdir(os.path.join(empty_dir, '.hg'))

    def fin():
        shutil.rmtree(empty_dir)
    request.addfinalizer(fin)

    repo = get_vcs_instance(empty_dir)

    assert repo is None


@mock.patch('rhodecode.lib.vcs.backends.get_scm')
@mock.patch('rhodecode.lib.vcs.backends.get_backend')
def test_get_vcs_instance_by_path_args_passed(
        get_backend_mock, get_scm_mock, tmpdir, vcs_repo):
    """
    Test that the arguments passed to ``get_vcs_instance_by_path`` are
    forwarded to the vcs backend class.
    """
    backend = mock.MagicMock()
    get_backend_mock.return_value = backend
    args = ['these-are-test-args', 0, True, None]
    repo = vcs_repo.path
    get_vcs_instance(repo, *args)

    backend.assert_called_with(*args, repo_path=repo)


@mock.patch('rhodecode.lib.vcs.backends.get_scm')
@mock.patch('rhodecode.lib.vcs.backends.get_backend')
def test_get_vcs_instance_by_path_kwargs_passed(
        get_backend_mock, get_scm_mock, vcs_repo):
    """
    Test that the keyword arguments passed to ``get_vcs_instance_by_path`` are
    forwarded to the vcs backend class.
    """
    backend = mock.MagicMock()
    get_backend_mock.return_value = backend
    kwargs = {
        'foo': 'these-are-test-args',
        'bar': 0,
        'baz': True,
        'foobar': None
    }
    repo = vcs_repo.path
    get_vcs_instance(repo, **kwargs)

    backend.assert_called_with(repo_path=repo, **kwargs)
