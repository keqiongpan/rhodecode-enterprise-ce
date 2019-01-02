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

import mock
import pytest
from rhodecode.model.db import Session, UserLog
from rhodecode.lib import hooks_base, utils2


def test_post_push_truncates_commits(user_regular, repo_stub):
    extras = {
        'ip': '127.0.0.1',
        'username': user_regular.username,
        'user_id': user_regular.user_id,
        'action': 'push_local',
        'repository': repo_stub.repo_name,
        'scm': 'git',
        'config': '',
        'server_url': 'http://example.com',
        'make_lock': None,
        'user_agent': 'some-client',
        'locked_by': [None],
        'commit_ids': ['abcde12345' * 4] * 30000,
        'hook_type': 'large_push_test_type',
        'is_shadow_repo': False,
    }
    extras = utils2.AttributeDict(extras)

    hooks_base.post_push(extras)

    # Calculate appropriate action string here
    commit_ids = extras.commit_ids[:400]

    entry = UserLog.query().order_by('-user_log_id').first()
    assert entry.action == 'user.push'
    assert entry.action_data['commit_ids'] == commit_ids
    Session().delete(entry)
    Session().commit()


def assert_called_with_mock(callable_, expected_mock_name):
    mock_obj = callable_.call_args[0][0]
    mock_name = mock_obj._mock_new_parent._mock_new_name
    assert mock_name == expected_mock_name


@pytest.fixture
def hook_extras(user_regular, repo_stub):
    extras = utils2.AttributeDict({
        'ip': '127.0.0.1',
        'username': user_regular.username,
        'user_id': user_regular.user_id,
        'action': 'push',
        'repository': repo_stub.repo_name,
        'scm': '',
        'config': '',
        'repo_store': '',
        'server_url': 'http://example.com',
        'make_lock': None,
        'user_agent': 'some-client',
        'locked_by': [None],
        'commit_ids': [],
        'hook_type': 'test_type',
        'is_shadow_repo': False,
    })
    return extras


@pytest.mark.parametrize('func, extension, event', [
    (hooks_base.pre_push, 'pre_push_extension', 'RepoPrePushEvent'),
    (hooks_base.post_push, 'post_pull_extension', 'RepoPushEvent'),
    (hooks_base.pre_pull, 'pre_pull_extension', 'RepoPrePullEvent'),
    (hooks_base.post_pull, 'post_push_extension', 'RepoPullEvent'),
])
def test_hooks_propagate(func, extension, event, hook_extras):
    """
    Tests that our hook code propagates to rhodecode extensions and triggers
    the appropriate event.
    """
    class ExtensionMock(mock.Mock):
        @property
        def output(self):
            return 'MOCK'

    extension_mock = ExtensionMock()
    events_mock = mock.Mock()
    patches = {
        'Repository': mock.Mock(),
        'events': events_mock,
        extension: extension_mock,
    }

    # Clear shadow repo flag.
    hook_extras.is_shadow_repo = False

    # Execute hook function.
    with mock.patch.multiple(hooks_base, **patches):
        func(hook_extras)

    # Assert that extensions are called and event was fired.
    extension_mock.called_once()
    assert_called_with_mock(events_mock.trigger, event)


@pytest.mark.parametrize('func, extension, event', [
    (hooks_base.pre_push, 'pre_push_extension', 'RepoPrePushEvent'),
    (hooks_base.post_push, 'post_pull_extension', 'RepoPushEvent'),
    (hooks_base.pre_pull, 'pre_pull_extension', 'RepoPrePullEvent'),
    (hooks_base.post_pull, 'post_push_extension', 'RepoPullEvent'),
])
def test_hooks_propagates_not_on_shadow(func, extension, event, hook_extras):
    """
    If hooks are called by a request to a shadow repo we only want to run our
    internal hooks code but not external ones like rhodecode extensions or
    trigger an event.
    """
    extension_mock = mock.Mock()
    events_mock = mock.Mock()
    patches = {
        'Repository': mock.Mock(),
        'events': events_mock,
        extension: extension_mock,
    }

    # Set shadow repo flag.
    hook_extras.is_shadow_repo = True

    # Execute hook function.
    with mock.patch.multiple(hooks_base, **patches):
        func(hook_extras)

    # Assert that extensions are *not* called and event was *not* fired.
    assert not extension_mock.called
    assert not events_mock.trigger.called
