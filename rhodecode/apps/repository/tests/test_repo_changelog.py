# -*- coding: utf-8 -*-

# Copyright (C) 2010-2019 RhodeCode GmbH
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

import re

import pytest

from rhodecode.apps.repository.views.repo_changelog import DEFAULT_CHANGELOG_SIZE
from rhodecode.tests import TestController

MATCH_HASH = re.compile(r'<span class="commit_hash">r(\d+):[\da-f]+</span>')


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'repo_changelog': '/{repo_name}/changelog',
        'repo_commits': '/{repo_name}/commits',
        'repo_commits_file': '/{repo_name}/commits/{commit_id}/{f_path}',
        'repo_commits_elements': '/{repo_name}/commits_elements',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


def assert_commits_on_page(response, indexes):
    found_indexes = [int(idx) for idx in MATCH_HASH.findall(response.body)]
    assert found_indexes == indexes


class TestChangelogController(TestController):

    def test_commits_page(self, backend):
        self.log_user()
        response = self.app.get(
            route_path('repo_commits', repo_name=backend.repo_name))

        first_idx = -1
        last_idx = -DEFAULT_CHANGELOG_SIZE
        self.assert_commit_range_on_page(response, first_idx, last_idx, backend)

    def test_changelog(self, backend):
        self.log_user()
        response = self.app.get(
            route_path('repo_changelog', repo_name=backend.repo_name))

        first_idx = -1
        last_idx = -DEFAULT_CHANGELOG_SIZE
        self.assert_commit_range_on_page(
            response, first_idx, last_idx, backend)

    @pytest.mark.backends("hg", "git")
    def test_changelog_filtered_by_branch(self, backend):
        self.log_user()
        self.app.get(
            route_path('repo_changelog', repo_name=backend.repo_name,
                       params=dict(branch=backend.default_branch_name)),
            status=200)

    @pytest.mark.backends("hg", "git")
    def test_commits_filtered_by_branch(self, backend):
        self.log_user()
        self.app.get(
            route_path('repo_commits', repo_name=backend.repo_name,
                       params=dict(branch=backend.default_branch_name)),
            status=200)

    @pytest.mark.backends("svn")
    def test_changelog_filtered_by_branch_svn(self, autologin_user, backend):
        repo = backend['svn-simple-layout']
        response = self.app.get(
            route_path('repo_changelog', repo_name=repo.repo_name,
                       params=dict(branch='trunk')),
            status=200)

        assert_commits_on_page(response, indexes=[15, 12, 7, 3, 2, 1])

    def test_commits_filtered_by_wrong_branch(self, backend):
        self.log_user()
        branch = 'wrong-branch-name'
        response = self.app.get(
            route_path('repo_commits', repo_name=backend.repo_name,
                       params=dict(branch=branch)),
            status=302)
        expected_url = '/{repo}/commits/{branch}'.format(
            repo=backend.repo_name, branch=branch)
        assert expected_url in response.location
        response = response.follow()
        expected_warning = 'Branch {} is not found.'.format(branch)
        assert expected_warning in response.body

    @pytest.mark.xfail_backends("svn", reason="Depends on branch support")
    def test_changelog_filtered_by_branch_with_merges(
            self, autologin_user, backend):

        # Note: The changelog of branch "b" does not contain the commit "a1"
        # although this is a parent of commit "b1". And branch "b" has commits
        # which have a smaller index than commit "a1".
        commits = [
            {'message': 'a'},
            {'message': 'b', 'branch': 'b'},
            {'message': 'a1', 'parents': ['a']},
            {'message': 'b1', 'branch': 'b', 'parents': ['b', 'a1']},
        ]
        backend.create_repo(commits)

        self.app.get(
            route_path('repo_changelog', repo_name=backend.repo_name,
                       params=dict(branch='b')),
            status=200)

    @pytest.mark.backends("hg")
    def test_commits_closed_branches(self, autologin_user, backend):
        repo = backend['closed_branch']
        response = self.app.get(
            route_path('repo_commits', repo_name=repo.repo_name,
                       params=dict(branch='experimental')),
            status=200)

        assert_commits_on_page(response, indexes=[3, 1])

    def test_changelog_pagination(self, backend):
        self.log_user()
        # pagination, walk up to page 6
        changelog_url = route_path(
            'repo_commits', repo_name=backend.repo_name)

        for page in range(1, 7):
            response = self.app.get(changelog_url, {'page': page})

        first_idx = -DEFAULT_CHANGELOG_SIZE * (page - 1) - 1
        last_idx = -DEFAULT_CHANGELOG_SIZE * page
        self.assert_commit_range_on_page(response, first_idx, last_idx, backend)

    def assert_commit_range_on_page(
            self, response, first_idx, last_idx, backend):
        input_template = (
            """<input class="commit-range" """ 
            """data-commit-id="%(raw_id)s" data-commit-idx="%(idx)s" """ 
            """data-short-id="%(short_id)s" id="%(raw_id)s" """
            """name="%(raw_id)s" type="checkbox" value="1" />"""
        )

        commit_span_template = """<span class="commit_hash">r%s:%s</span>"""
        repo = backend.repo

        first_commit_on_page = repo.get_commit(commit_idx=first_idx)
        response.mustcontain(
            input_template % {'raw_id': first_commit_on_page.raw_id,
                              'idx': first_commit_on_page.idx,
                              'short_id': first_commit_on_page.short_id})

        response.mustcontain(commit_span_template % (
            first_commit_on_page.idx, first_commit_on_page.short_id)
        )

        last_commit_on_page = repo.get_commit(commit_idx=last_idx)
        response.mustcontain(
            input_template % {'raw_id': last_commit_on_page.raw_id,
                              'idx': last_commit_on_page.idx,
                              'short_id': last_commit_on_page.short_id})
        response.mustcontain(commit_span_template % (
            last_commit_on_page.idx, last_commit_on_page.short_id)
        )

        first_commit_of_next_page = repo.get_commit(commit_idx=last_idx - 1)
        first_span_of_next_page = commit_span_template % (
            first_commit_of_next_page.idx, first_commit_of_next_page.short_id)
        assert first_span_of_next_page not in response

    @pytest.mark.parametrize('test_path', [
        'vcs/exceptions.py',
        '/vcs/exceptions.py',
        '//vcs/exceptions.py'
    ])
    def test_commits_with_filenode(self, backend, test_path):
        self.log_user()
        response = self.app.get(
            route_path('repo_commits_file', repo_name=backend.repo_name,
                       commit_id='tip', f_path=test_path),
            )

        # history commits messages
        response.mustcontain('Added exceptions module, this time for real')
        response.mustcontain('Added not implemented hg backend test case')
        response.mustcontain('Added BaseChangeset class')

    def test_commits_with_filenode_that_is_dirnode(self, backend):
        self.log_user()
        self.app.get(
            route_path('repo_commits_file', repo_name=backend.repo_name,
                       commit_id='tip', f_path='/tests'),
            status=302)

    def test_commits_with_filenode_not_existing(self, backend):
        self.log_user()
        self.app.get(
            route_path('repo_commits_file', repo_name=backend.repo_name,
                       commit_id='tip', f_path='wrong_path'),
            status=302)
