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
from rhodecode import events
from rhodecode.lib.utils2 import AttributeDict


@pytest.fixture
def repo_push_event(backend, user_regular):
    commits = [
        {'message': 'ancestor commit fixes #15'},
        {'message': 'quick fixes'},
        {'message': 'change that fixes #41, #2'},
        {'message': 'this is because 5b23c3532 broke stuff'},
        {'message': 'last commit'},
    ]
    commit_ids = backend.create_master_repo(commits).values()
    repo = backend.create_repo()
    scm_extras = AttributeDict({
        'ip': '127.0.0.1',
        'username': user_regular.username,
        'user_id': user_regular.user_id,
        'action': '',
        'repository': repo.repo_name,
        'scm': repo.scm_instance().alias,
        'config': '',
        'repo_store': '',
        'server_url': 'http://example.com',
        'make_lock': None,
        'locked_by': [None],
        'commit_ids': commit_ids,
    })

    return events.RepoPushEvent(repo_name=repo.repo_name,
                                pushed_commit_ids=commit_ids,
                                extras=scm_extras)
