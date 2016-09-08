# -*- coding: utf-8 -*-

# Copyright (C) 2010-2016  RhodeCode GmbH
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

from rhodecode.lib.vcs import nodes
from rhodecode.model.repo import ReadmeFinder


@pytest.fixture
def commit_util(vcsbackend_stub):
    """
    Provide a commit which has certain files in it's tree.

    This is based on the fixture "vcsbackend" and will automatically be
    parametrized for all vcs backends.
    """
    return CommitUtility(vcsbackend_stub)


class CommitUtility:

    def __init__(self, vcsbackend):
        self.vcsbackend = vcsbackend

    def commit_with_files(self, filenames):
        commits = [
            {'message': 'Adding all requested files',
             'added': [
                 nodes.FileNode(filename, content='')
                 for filename in filenames
             ]}]
        repo = self.vcsbackend.create_repo(commits=commits)
        return repo.get_commit()


def test_no_matching_file_returns_none(commit_util):
    commit = commit_util.commit_with_files(['LIESMICH'])
    finder = ReadmeFinder(default_renderer='rst')
    filenode = finder.search(commit)
    assert filenode is None


def test_matching_file_returns_the_file_name(commit_util):
    commit = commit_util.commit_with_files(['README'])
    finder = ReadmeFinder(default_renderer='rst')
    filenode = finder.search(commit)
    assert filenode.path == 'README'


def test_matching_file_with_extension(commit_util):
    commit = commit_util.commit_with_files(['README.rst'])
    finder = ReadmeFinder(default_renderer='rst')
    filenode = finder.search(commit)
    assert filenode.path == 'README.rst'


def test_prefers_readme_without_extension(commit_util):
    commit = commit_util.commit_with_files(['README.rst', 'Readme'])
    finder = ReadmeFinder()
    filenode = finder.search(commit)
    assert filenode.path == 'Readme'


@pytest.mark.parametrize('renderer, expected', [
    ('rst', 'readme.rst'),
    ('markdown', 'readme.md'),
])
def test_prefers_renderer_extensions(commit_util, renderer, expected):
    commit = commit_util.commit_with_files(
        ['readme.rst', 'readme.md', 'readme.txt'])
    finder = ReadmeFinder(default_renderer=renderer)
    filenode = finder.search(commit)
    assert filenode.path == expected


def test_finds_readme_in_subdirectory(commit_util):
    commit = commit_util.commit_with_files(['doc/README.rst', 'LIESMICH'])
    finder = ReadmeFinder()
    filenode = finder.search(commit)
    assert filenode.path == 'doc/README.rst'


def test_prefers_subdirectory_with_priority(commit_util):
    commit = commit_util.commit_with_files(
        ['Doc/Readme.rst', 'Docs/Readme.rst'])
    finder = ReadmeFinder()
    filenode = finder.search(commit)
    assert filenode.path == 'Doc/Readme.rst'
