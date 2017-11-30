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
from mock import Mock, patch

from rhodecode.lib import base
from rhodecode.model import db


@pytest.mark.parametrize('result_key, expected_value', [
    ('username', 'stub_username'),
    ('action', 'stub_action'),
    ('repository', 'stub_repo_name'),
    ('scm', 'stub_scm'),
    ('hooks', ['stub_hook']),
    ('config', 'stub_ini_filename'),
    ('ip', '1.2.3.4'),
    ('server_url', 'https://example.com'),
    ('user_agent', 'client-text-v1.1'),
    # TODO: johbo: Commpare locking parameters with `_get_rc_scm_extras`
    # in hooks_utils.
    ('make_lock', None),
    ('locked_by', [None, None, None]),
])
def test_vcs_operation_context_parameters(result_key, expected_value):
    result = call_vcs_operation_context()
    assert result[result_key] == expected_value


@patch('rhodecode.model.db.User.get_by_username', Mock())
@patch('rhodecode.model.db.Repository.get_by_repo_name')
def test_vcs_operation_context_checks_locking(mock_get_by_repo_name):
    mock_get_locking_state = mock_get_by_repo_name().get_locking_state
    mock_get_locking_state.return_value = (None, None, [None, None, None])
    call_vcs_operation_context(check_locking=True)
    assert mock_get_locking_state.called


@patch('rhodecode.model.db.Repository.get_locking_state')
def test_vcs_operation_context_skips_locking_checks_if_anonymouse(
        mock_get_locking_state):
    call_vcs_operation_context(
        username=db.User.DEFAULT_USER, check_locking=True)
    assert not mock_get_locking_state.called


@patch('rhodecode.model.db.Repository.get_locking_state')
def test_vcs_operation_context_can_skip_locking_check(mock_get_locking_state):
    call_vcs_operation_context(check_locking=False)
    assert not mock_get_locking_state.called


@patch.object(
    base, 'get_enabled_hook_classes', Mock(return_value=['stub_hook']))
@patch('rhodecode.lib.utils2.get_server_url',
       Mock(return_value='https://example.com'))
@patch.object(db.User, 'get_by_username',
       Mock(return_value=Mock(return_value=1)))
def call_vcs_operation_context(**kwargs_override):
    kwargs = {
        'repo_name': 'stub_repo_name',
        'username': 'stub_username',
        'action': 'stub_action',
        'scm': 'stub_scm',
        'check_locking': False,
    }
    kwargs.update(kwargs_override)
    config_file_patch = patch.dict(
        'rhodecode.CONFIG', {'__file__': 'stub_ini_filename'})
    settings_patch = patch.object(base, 'VcsSettingsModel')
    with config_file_patch, settings_patch as settings_mock:
        result = base.vcs_operation_context(
            environ={'HTTP_USER_AGENT': 'client-text-v1.1',
                     'REMOTE_ADDR': '1.2.3.4'}, **kwargs)
    settings_mock.assert_called_once_with(repo='stub_repo_name')
    return result


