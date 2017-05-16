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

import pytest

from rhodecode.lib.utils2 import safe_unicode, safe_str
from rhodecode.model.db import Repository
from rhodecode.model.repo import RepoModel
from rhodecode.tests import (
    HG_REPO, GIT_REPO, assert_session_flash, no_newline_id_generator)
from rhodecode.tests.fixture import Fixture
from rhodecode.tests.utils import repo_on_filesystem

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'repo_summary_explicit': '/{repo_name}/summary',
        'repo_summary': '/{repo_name}',
        'edit_repo_advanced': '/{repo_name}/settings/advanced',
        'edit_repo_advanced_delete': '/{repo_name}/settings/advanced/delete',
        'edit_repo_advanced_fork': '/{repo_name}/settings/advanced/fork',
        'edit_repo_advanced_locking': '/{repo_name}/settings/advanced/locking',
        'edit_repo_advanced_journal': '/{repo_name}/settings/advanced/journal',

    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.usefixtures('autologin_user', 'app')
class TestAdminRepoSettingsAdvanced(object):

    def test_set_repo_fork_has_no_self_id(self, autologin_user, backend):
        repo = backend.repo
        response = self.app.get(
            route_path('edit_repo_advanced', repo_name=backend.repo_name))
        opt = """<option value="%s">vcs_test_git</option>""" % repo.repo_id
        response.mustcontain(no=[opt])

    def test_set_fork_of_target_repo(
            self, autologin_user, backend, csrf_token):
        target_repo = 'target_%s' % backend.alias
        fixture.create_repo(target_repo, repo_type=backend.alias)
        repo2 = Repository.get_by_repo_name(target_repo)
        response = self.app.post(
            route_path('edit_repo_advanced_fork', repo_name=backend.repo_name),
            params={'id_fork_of': repo2.repo_id,
                    'csrf_token': csrf_token})
        repo = Repository.get_by_repo_name(backend.repo_name)
        repo2 = Repository.get_by_repo_name(target_repo)
        assert_session_flash(
            response,
            'Marked repo %s as fork of %s' % (repo.repo_name, repo2.repo_name))

        assert repo.fork == repo2
        response = response.follow()
        # check if given repo is selected

        opt = 'This repository is a fork of <a href="%s">%s</a>' % (
            route_path('repo_summary', repo_name=repo2.repo_name),
            repo2.repo_name)

        response.mustcontain(opt)

        fixture.destroy_repo(target_repo, forks='detach')

    @pytest.mark.backends("hg", "git")
    def test_set_fork_of_other_type_repo(
            self, autologin_user, backend, csrf_token):
        TARGET_REPO_MAP = {
            'git': {
                'type': 'hg',
                'repo_name': HG_REPO},
            'hg': {
                'type': 'git',
                'repo_name': GIT_REPO},
        }
        target_repo = TARGET_REPO_MAP[backend.alias]

        repo2 = Repository.get_by_repo_name(target_repo['repo_name'])
        response = self.app.post(
            route_path('edit_repo_advanced_fork', repo_name=backend.repo_name),
            params={'id_fork_of': repo2.repo_id,
                    'csrf_token': csrf_token})
        assert_session_flash(
            response,
            'Cannot set repository as fork of repository with other type')

    def test_set_fork_of_none(self, autologin_user, backend, csrf_token):
        # mark it as None
        response = self.app.post(
            route_path('edit_repo_advanced_fork', repo_name=backend.repo_name),
            params={'id_fork_of': None, '_method': 'put',
                    'csrf_token': csrf_token})
        assert_session_flash(
            response,
            'Marked repo %s as fork of %s'
            % (backend.repo_name, "Nothing"))
        assert backend.repo.fork is None

    def test_set_fork_of_same_repo(self, autologin_user, backend, csrf_token):
        repo = Repository.get_by_repo_name(backend.repo_name)
        response = self.app.post(
            route_path('edit_repo_advanced_fork', repo_name=backend.repo_name),
            params={'id_fork_of': repo.repo_id, 'csrf_token': csrf_token})
        assert_session_flash(
            response, 'An error occurred during this operation')

    @pytest.mark.parametrize(
        "suffix",
        ['', u'ąęł' , '123'],
        ids=no_newline_id_generator)
    def test_advanced_delete(self, autologin_user, backend, suffix, csrf_token):
        repo = backend.create_repo(name_suffix=suffix)
        repo_name = repo.repo_name
        repo_name_str = safe_str(repo.repo_name)

        response = self.app.post(
            route_path('edit_repo_advanced_delete', repo_name=repo_name_str),
            params={'csrf_token': csrf_token})
        assert_session_flash(response,
                             u'Deleted repository `{}`'.format(repo_name))
        response.follow()

        # check if repo was deleted from db
        assert RepoModel().get_by_repo_name(repo_name) is None
        assert not repo_on_filesystem(repo_name_str)
