# Copyright (C) 2016-2020 RhodeCode GmbH
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
rcextensions module, please edit `hooks.py` to over write hooks logic
"""

from .hooks import (
    _create_repo_hook,
    _create_repo_group_hook,
    _pre_create_user_hook,
    _create_user_hook,
    _comment_commit_repo_hook,
    _comment_edit_commit_repo_hook,
    _delete_repo_hook,
    _delete_user_hook,
    _pre_push_hook,
    _push_hook,
    _pre_pull_hook,
    _pull_hook,
    _create_pull_request_hook,
    _review_pull_request_hook,
    _comment_pull_request_hook,
    _comment_edit_pull_request_hook,
    _update_pull_request_hook,
    _merge_pull_request_hook,
    _close_pull_request_hook,
)

# set as module attributes, we use those to call hooks. *do not change this*
CREATE_REPO_HOOK = _create_repo_hook
COMMENT_COMMIT_REPO_HOOK = _comment_commit_repo_hook
COMMENT_EDIT_COMMIT_REPO_HOOK = _comment_edit_commit_repo_hook
CREATE_REPO_GROUP_HOOK = _create_repo_group_hook
PRE_CREATE_USER_HOOK = _pre_create_user_hook
CREATE_USER_HOOK = _create_user_hook
DELETE_REPO_HOOK = _delete_repo_hook
DELETE_USER_HOOK = _delete_user_hook
PRE_PUSH_HOOK = _pre_push_hook
PUSH_HOOK = _push_hook
PRE_PULL_HOOK = _pre_pull_hook
PULL_HOOK = _pull_hook
CREATE_PULL_REQUEST = _create_pull_request_hook
REVIEW_PULL_REQUEST = _review_pull_request_hook
COMMENT_PULL_REQUEST = _comment_pull_request_hook
COMMENT_EDIT_PULL_REQUEST = _comment_edit_pull_request_hook
UPDATE_PULL_REQUEST = _update_pull_request_hook
MERGE_PULL_REQUEST = _merge_pull_request_hook
CLOSE_PULL_REQUEST = _close_pull_request_hook
