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

import os
import stat
import sys

import pytest
from mock import Mock, patch, DEFAULT

import rhodecode
from rhodecode.model import db, scm
from rhodecode.tests import no_newline_id_generator


def test_scm_instance_config(backend):
    repo = backend.create_repo()
    with patch.multiple('rhodecode.model.db.Repository',
                        _get_instance=DEFAULT,
                        _get_instance_cached=DEFAULT) as mocks:
        repo.scm_instance()
        mocks['_get_instance'].assert_called_with(
            config=None, cache=False)

        config = {'some': 'value'}
        repo.scm_instance(config=config)
        mocks['_get_instance'].assert_called_with(
            config=config, cache=False)

        with patch.dict(rhodecode.CONFIG, {'vcs_full_cache': 'true'}):
            repo.scm_instance(config=config)
            mocks['_get_instance_cached'].assert_called()


def test__get_instance_config(backend):
    repo = backend.create_repo()
    vcs_class = Mock()
    with patch.multiple('rhodecode.lib.vcs.backends',
                        get_scm=DEFAULT,
                        get_backend=DEFAULT) as mocks:
        mocks['get_scm'].return_value = backend.alias
        mocks['get_backend'].return_value = vcs_class
        with patch('rhodecode.model.db.Repository._config') as config_mock:
            repo._get_instance()
            vcs_class.assert_called_with(
                repo_path=repo.repo_full_path, config=config_mock,
                create=False, with_wire={'cache': True})

        new_config = {'override': 'old_config'}
        repo._get_instance(config=new_config)
        vcs_class.assert_called_with(
            repo_path=repo.repo_full_path, config=new_config, create=False,
            with_wire={'cache': True})


def test_mark_for_invalidation_config(backend):
    repo = backend.create_repo()
    with patch('rhodecode.model.db.Repository.update_commit_cache') as _mock:
        scm.ScmModel().mark_for_invalidation(repo.repo_name)
        _, kwargs = _mock.call_args
        assert kwargs['config'].__dict__ == repo._config.__dict__


def test_mark_for_invalidation_with_delete_updates_last_commit(backend):
    commits = [{'message': 'A'}, {'message': 'B'}]
    repo = backend.create_repo(commits=commits)
    scm.ScmModel().mark_for_invalidation(repo.repo_name, delete=True)
    assert repo.changeset_cache['revision'] == 1


def test_mark_for_invalidation_with_delete_updates_last_commit_empty(backend):
    repo = backend.create_repo()
    scm.ScmModel().mark_for_invalidation(repo.repo_name, delete=True)
    assert repo.changeset_cache['revision'] == -1


def test_strip_with_multiple_heads(backend_hg):
    commits = [
        {'message': 'A'},
        {'message': 'a'},
        {'message': 'b'},
        {'message': 'B', 'parents': ['A']},
        {'message': 'a1'},
    ]
    repo = backend_hg.create_repo(commits=commits)
    commit_ids = backend_hg.commit_ids

    model = scm.ScmModel()
    model.strip(repo, commit_ids['b'], branch=None)

    vcs_repo = repo.scm_instance()
    rest_commit_ids = [c.raw_id for c in vcs_repo.get_changesets()]
    assert len(rest_commit_ids) == 4
    assert commit_ids['b'] not in rest_commit_ids


def test_strip_with_single_heads(backend_hg):
    commits = [
        {'message': 'A'},
        {'message': 'a'},
        {'message': 'b'},
    ]
    repo = backend_hg.create_repo(commits=commits)
    commit_ids = backend_hg.commit_ids

    model = scm.ScmModel()
    model.strip(repo, commit_ids['b'], branch=None)

    vcs_repo = repo.scm_instance()
    rest_commit_ids = [c.raw_id for c in vcs_repo.get_changesets()]
    assert len(rest_commit_ids) == 2
    assert commit_ids['b'] not in rest_commit_ids


def test_get_nodes_returns_unicode_flat(backend_random):
    repo = backend_random.repo
    directories, files = scm.ScmModel().get_nodes(
        repo.repo_name, repo.get_commit(commit_idx=0).raw_id,
        flat=True)
    assert_contains_only_unicode(directories)
    assert_contains_only_unicode(files)


def test_get_nodes_returns_unicode_non_flat(backend_random):
    repo = backend_random.repo
    directories, files = scm.ScmModel().get_nodes(
        repo.repo_name, repo.get_commit(commit_idx=0).raw_id,
        flat=False)
    # johbo: Checking only the names for now, since that is the critical
    # part.
    assert_contains_only_unicode([d['name'] for d in directories])
    assert_contains_only_unicode([f['name'] for f in files])


def test_get_nodes_max_file_bytes(backend_random):
    repo = backend_random.repo
    max_file_bytes = 10
    directories, files = scm.ScmModel().get_nodes(
        repo.repo_name, repo.get_commit(commit_idx=0).raw_id, content=True,
        extended_info=True, flat=False)
    assert any(file['content'] and len(file['content']) > max_file_bytes
               for file in files)

    directories, files = scm.ScmModel().get_nodes(
        repo.repo_name, repo.get_commit(commit_idx=0).raw_id, content=True,
        extended_info=True, flat=False, max_file_bytes=max_file_bytes)
    assert all(
        file['content'] is None if file['size'] > max_file_bytes else True
        for file in files)


def assert_contains_only_unicode(structure):
    assert structure
    for value in structure:
        assert isinstance(value, unicode)


@pytest.mark.backends("hg", "git")
def test_get_non_unicode_reference(backend):
    model = scm.ScmModel()
    non_unicode_list = ["Adını".decode("cp1254")]

    def scm_instance():
        return Mock(
            branches=non_unicode_list, bookmarks=non_unicode_list,
            tags=non_unicode_list, alias=backend.alias)

    repo = Mock(__class__=db.Repository, scm_instance=scm_instance)
    choices, __ = model.get_repo_landing_revs(translator=lambda s: s, repo=repo)
    if backend.alias == 'hg':
        valid_choices = [
            'rev:tip', u'branch:Ad\xc4\xb1n\xc4\xb1',
            u'book:Ad\xc4\xb1n\xc4\xb1', u'tag:Ad\xc4\xb1n\xc4\xb1']
    else:
        valid_choices = [
            'rev:tip', u'branch:Ad\xc4\xb1n\xc4\xb1',
            u'tag:Ad\xc4\xb1n\xc4\xb1']

    assert choices == valid_choices
