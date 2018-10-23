# -*- coding: utf-8 -*-
# Copyright (C) 2016-2018 RhodeCode GmbH
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
us in hooks::

    from .helpers import extract_pre_commits
    # returns list of dicts with key-val fetched from extra fields
    commit_list = extract_pre_commits.run(**kwargs)

"""
import re
import collections


def get_hg_commits(repo, refs):
    commits = []
    return commits


def get_git_commits(repo, refs):
    commits = []
    return commits


def run(*args, **kwargs):
    from rhodecode.model.db import Repository

    vcs_type = kwargs['scm']
    # use temp name then the main one propagated
    repo_name = kwargs.pop('REPOSITORY', None) or kwargs['repository']

    repo = Repository.get_by_repo_name(repo_name)
    vcs_repo = repo.scm_instance(cache=False)

    commits = []

    for rev_data in kwargs['commit_ids']:
        new_environ = dict((k, v) for k, v in rev_data['hg_env'])

    if vcs_type == 'git':
        commits = get_git_commits(vcs_repo, kwargs['commit_ids'])

    if vcs_type == 'hg':
        commits = get_hg_commits(vcs_repo, kwargs['commit_ids'])

    return commits
