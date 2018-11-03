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
Extract and serialize commits taken from a list of commit_ids. This should
be used in post_push hook

us in hooks::

    from .helpers import extract_post_commits
    # returns list of dicts with key-val fetched from extra fields
    commit_list = extract_post_commits.run(**kwargs)
"""
import traceback


def run(*args, **kwargs):
    from rhodecode.lib.utils2 import extract_mentioned_users
    from rhodecode.model.db import Repository

    commit_ids = kwargs.get('commit_ids')
    if not commit_ids:
        return 0

    # use temp name then the main one propagated
    repo_name = kwargs.pop('REPOSITORY', None) or kwargs['repository']

    repo = Repository.get_by_repo_name(repo_name)
    commits = []

    vcs_repo = repo.scm_instance(cache=False)
    try:
        for commit_id in commit_ids:
            cs = vcs_repo.get_changeset(commit_id)
            cs_data = cs.__json__()
            cs_data['mentions'] = extract_mentioned_users(cs_data['message'])
            # optionally add more logic to parse the commits, like reading extra
            # fields of repository to read managers of reviewers ?
            commits.append(cs_data)
    except Exception:
        print(traceback.format_exc())
        # we don't send any commits when crash happens, only full list matters
        # we short circuit then.
        return []
    return commits
