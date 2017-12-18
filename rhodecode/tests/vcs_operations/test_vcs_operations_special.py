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

import os

import pytest

from rhodecode.lib.vcs.backends.git.repository import GitRepository
from rhodecode.lib.vcs.backends.hg.repository import MercurialRepository
from rhodecode.lib.vcs.nodes import FileNode
from rhodecode.model.meta import Session

from rhodecode.tests.vcs_operations import (
    Command, _check_proper_clone, _check_proper_git_push, _check_proper_hg_push)


@pytest.mark.usefixtures("disable_locking")
class TestVCSOperationsSpecial(object):

    def test_git_sets_default_branch_if_not_master(
            self, backend_git, tmpdir, rc_web_server):
        empty_repo = backend_git.create_repo()
        clone_url = rc_web_server.repo_clone_url(empty_repo.repo_name)

        cmd = Command(tmpdir.strpath)
        cmd.execute('git clone', clone_url)

        repo = GitRepository(os.path.join(tmpdir.strpath, empty_repo.repo_name))
        repo.in_memory_commit.add(FileNode('file', content=''))
        repo.in_memory_commit.commit(
            message='Commit on branch test',
            author='Automatic test',
            branch='test')

        repo_cmd = Command(repo.path)
        stdout, stderr = repo_cmd.execute('git push --verbose origin test')
        _check_proper_git_push(
            stdout, stderr, branch='test', should_set_default_branch=True)

        stdout, stderr = cmd.execute(
            'git clone', clone_url, empty_repo.repo_name + '-clone')
        _check_proper_clone(stdout, stderr, 'git')

        # Doing an explicit commit in order to get latest user logs on MySQL
        Session().commit()

    def test_git_fetches_from_remote_repository_with_annotated_tags(
            self, backend_git, rc_web_server):
        # Note: This is a test specific to the git backend. It checks the
        # integration of fetching from a remote repository which contains
        # annotated tags.

        # Dulwich shows this specific behavior only when
        # operating against a remote repository.
        source_repo = backend_git['annotated-tag']
        target_vcs_repo = backend_git.create_repo().scm_instance()
        target_vcs_repo.fetch(rc_web_server.repo_clone_url(source_repo.repo_name))

    def test_git_push_shows_pull_request_refs(self, backend_git, rc_web_server, tmpdir):
        """
        test if remote info about refs is visible
        """
        empty_repo = backend_git.create_repo()

        clone_url = rc_web_server.repo_clone_url(empty_repo.repo_name)

        cmd = Command(tmpdir.strpath)
        cmd.execute('git clone', clone_url)

        repo = GitRepository(os.path.join(tmpdir.strpath, empty_repo.repo_name))
        repo.in_memory_commit.add(FileNode('readme.md', content='## Hello'))
        repo.in_memory_commit.commit(
            message='Commit on branch Master',
            author='Automatic test',
            branch='master')

        repo_cmd = Command(repo.path)
        stdout, stderr = repo_cmd.execute('git push --verbose origin master')
        _check_proper_git_push(stdout, stderr, branch='master')

        ref = '{}/{}/pull-request/new?branch=master'.format(
            rc_web_server.host_url(), empty_repo.repo_name)
        assert 'remote: RhodeCode: open pull request link: {}'.format(ref) in stderr
        assert 'remote: RhodeCode: push completed' in stderr

        # push on the same branch
        repo = GitRepository(os.path.join(tmpdir.strpath, empty_repo.repo_name))
        repo.in_memory_commit.add(FileNode('setup.py', content='print\n'))
        repo.in_memory_commit.commit(
            message='Commit2 on branch Master',
            author='Automatic test2',
            branch='master')

        repo_cmd = Command(repo.path)
        stdout, stderr = repo_cmd.execute('git push --verbose origin master')
        _check_proper_git_push(stdout, stderr, branch='master')

        assert 'remote: RhodeCode: open pull request link: {}'.format(ref) in stderr
        assert 'remote: RhodeCode: push completed' in stderr

        # new Branch
        repo = GitRepository(os.path.join(tmpdir.strpath, empty_repo.repo_name))
        repo.in_memory_commit.add(FileNode('feature1.py', content='## Hello world'))
        repo.in_memory_commit.commit(
            message='Commit on branch feature',
            author='Automatic test',
            branch='feature')

        repo_cmd = Command(repo.path)
        stdout, stderr = repo_cmd.execute('git push --verbose origin feature')
        _check_proper_git_push(stdout, stderr, branch='feature')

        ref = '{}/{}/pull-request/new?branch=feature'.format(
            rc_web_server.host_url(), empty_repo.repo_name)
        assert 'remote: RhodeCode: open pull request link: {}'.format(ref) in stderr
        assert 'remote: RhodeCode: push completed' in stderr

    def test_hg_push_shows_pull_request_refs(self, backend_hg, rc_web_server, tmpdir):
        empty_repo = backend_hg.create_repo()

        clone_url = rc_web_server.repo_clone_url(empty_repo.repo_name)

        cmd = Command(tmpdir.strpath)
        cmd.execute('hg clone', clone_url)

        repo = MercurialRepository(os.path.join(tmpdir.strpath, empty_repo.repo_name))
        repo.in_memory_commit.add(FileNode(u'readme.md', content=u'## Hello'))
        repo.in_memory_commit.commit(
            message=u'Commit on branch default',
            author=u'Automatic test',
            branch='default')

        repo_cmd = Command(repo.path)
        repo_cmd.execute('hg checkout default')

        stdout, stderr = repo_cmd.execute('hg push --verbose', clone_url)
        _check_proper_hg_push(stdout, stderr, branch='default')

        ref = '{}/{}/pull-request/new?branch=default'.format(
            rc_web_server.host_url(), empty_repo.repo_name)
        assert 'remote: RhodeCode: open pull request link: {}'.format(ref) in stdout
        assert 'remote: RhodeCode: push completed' in stdout

        # push on the same branch
        repo = MercurialRepository(os.path.join(tmpdir.strpath, empty_repo.repo_name))
        repo.in_memory_commit.add(FileNode(u'setup.py', content=u'print\n'))
        repo.in_memory_commit.commit(
            message=u'Commit2 on branch default',
            author=u'Automatic test2',
            branch=u'default')

        repo_cmd = Command(repo.path)
        repo_cmd.execute('hg checkout default')

        stdout, stderr = repo_cmd.execute('hg push --verbose', clone_url)
        _check_proper_hg_push(stdout, stderr, branch='default')

        assert 'remote: RhodeCode: open pull request link: {}'.format(ref) in stdout
        assert 'remote: RhodeCode: push completed' in stdout

        # new Branch
        repo = MercurialRepository(os.path.join(tmpdir.strpath, empty_repo.repo_name))
        repo.in_memory_commit.add(FileNode(u'feature1.py', content=u'## Hello world'))
        repo.in_memory_commit.commit(
            message=u'Commit on branch feature',
            author=u'Automatic test',
            branch=u'feature')

        repo_cmd = Command(repo.path)
        repo_cmd.execute('hg checkout feature')

        stdout, stderr = repo_cmd.execute('hg push --new-branch --verbose', clone_url)
        _check_proper_hg_push(stdout, stderr, branch='feature')

        ref = '{}/{}/pull-request/new?branch=feature'.format(
            rc_web_server.host_url(), empty_repo.repo_name)
        assert 'remote: RhodeCode: open pull request link: {}'.format(ref) in stdout
        assert 'remote: RhodeCode: push completed' in stdout

    def test_hg_push_shows_pull_request_refs_book(self, backend_hg, rc_web_server, tmpdir):
        empty_repo = backend_hg.create_repo()

        clone_url = rc_web_server.repo_clone_url(empty_repo.repo_name)

        cmd = Command(tmpdir.strpath)
        cmd.execute('hg clone', clone_url)

        repo = MercurialRepository(os.path.join(tmpdir.strpath, empty_repo.repo_name))
        repo.in_memory_commit.add(FileNode(u'readme.md', content=u'## Hello'))
        repo.in_memory_commit.commit(
            message=u'Commit on branch default',
            author=u'Automatic test',
            branch='default')

        repo_cmd = Command(repo.path)
        repo_cmd.execute('hg checkout default')

        stdout, stderr = repo_cmd.execute('hg push --verbose', clone_url)
        _check_proper_hg_push(stdout, stderr, branch='default')

        ref = '{}/{}/pull-request/new?branch=default'.format(
            rc_web_server.host_url(), empty_repo.repo_name)
        assert 'remote: RhodeCode: open pull request link: {}'.format(ref) in stdout
        assert 'remote: RhodeCode: push completed' in stdout

        # add bookmark
        repo = MercurialRepository(os.path.join(tmpdir.strpath, empty_repo.repo_name))
        repo.in_memory_commit.add(FileNode(u'setup.py', content=u'print\n'))
        repo.in_memory_commit.commit(
            message=u'Commit2 on branch default',
            author=u'Automatic test2',
            branch=u'default')

        repo_cmd = Command(repo.path)
        repo_cmd.execute('hg checkout default')
        repo_cmd.execute('hg bookmark feature2')
        stdout, stderr = repo_cmd.execute('hg push -B feature2 --verbose', clone_url)
        _check_proper_hg_push(stdout, stderr, branch='default')

        ref = '{}/{}/pull-request/new?branch=default'.format(
            rc_web_server.host_url(), empty_repo.repo_name)
        assert 'remote: RhodeCode: open pull request link: {}'.format(ref) in stdout
        ref = '{}/{}/pull-request/new?bookmark=feature2'.format(
            rc_web_server.host_url(), empty_repo.repo_name)
        assert 'remote: RhodeCode: open pull request link: {}'.format(ref) in stdout
        assert 'remote: RhodeCode: push completed' in stdout
        assert 'exporting bookmark feature2' in stdout
