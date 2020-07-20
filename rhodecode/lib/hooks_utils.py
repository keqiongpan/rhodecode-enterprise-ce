# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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

import webob
from pyramid.threadlocal import get_current_request

from rhodecode import events
from rhodecode.lib import hooks_base
from rhodecode.lib import utils2


def _supports_repo_type(repo_type):
    if repo_type in ('hg', 'git'):
        return True
    return False


def _get_vcs_operation_context(username, repo_name, repo_type, action):
    # NOTE(dan): import loop
    from rhodecode.lib.base import vcs_operation_context

    check_locking = action in ('pull', 'push')

    request = get_current_request()

    try:
        environ = request.environ
    except TypeError:
        # we might use this outside of request context
        environ = {}

    if not environ:
        environ = webob.Request.blank('').environ

    extras = vcs_operation_context(environ, repo_name, username, action, repo_type, check_locking)
    return utils2.AttributeDict(extras)


def trigger_post_push_hook(username, action, hook_type, repo_name, repo_type, commit_ids):
    """
    Triggers push action hooks

    :param username: username who pushes
    :param action: push/push_local/push_remote
    :param hook_type: type of hook executed
    :param repo_name: name of repo
    :param repo_type: the type of SCM repo
    :param commit_ids: list of commit ids that we pushed
    """
    extras = _get_vcs_operation_context(username, repo_name, repo_type, action)
    extras.commit_ids = commit_ids
    extras.hook_type = hook_type
    hooks_base.post_push(extras)


def trigger_comment_commit_hooks(username, repo_name, repo_type, repo, data=None):
    """
    Triggers when a comment is made on a commit

    :param username: username who creates the comment
    :param repo_name: name of target repo
    :param repo_type: the type of SCM target repo
    :param repo: the repo object we trigger the event for
    :param data: extra data for specific events e.g {'comment': comment_obj, 'commit': commit_obj}
    """
    if not _supports_repo_type(repo_type):
        return

    extras = _get_vcs_operation_context(username, repo_name, repo_type, 'comment_commit')

    comment = data['comment']
    commit = data['commit']

    events.trigger(events.RepoCommitCommentEvent(repo, commit, comment))
    extras.update(repo.get_dict())

    extras.commit = commit.serialize()
    extras.comment = comment.get_api_data()
    extras.created_by = username
    hooks_base.comment_commit_repository(**extras)


def trigger_comment_commit_edit_hooks(username, repo_name, repo_type, repo, data=None):
    """
    Triggers when a comment is edited on a commit

    :param username: username who edits the comment
    :param repo_name: name of target repo
    :param repo_type: the type of SCM target repo
    :param repo: the repo object we trigger the event for
    :param data: extra data for specific events e.g {'comment': comment_obj, 'commit': commit_obj}
    """
    if not _supports_repo_type(repo_type):
        return

    extras = _get_vcs_operation_context(username, repo_name, repo_type, 'comment_commit')

    comment = data['comment']
    commit = data['commit']

    events.trigger(events.RepoCommitCommentEditEvent(repo, commit, comment))
    extras.update(repo.get_dict())

    extras.commit = commit.serialize()
    extras.comment = comment.get_api_data()
    extras.created_by = username
    hooks_base.comment_edit_commit_repository(**extras)


def trigger_create_pull_request_hook(username, repo_name, repo_type, pull_request, data=None):
    """
    Triggers create pull request action hooks

    :param username: username who creates the pull request
    :param repo_name: name of target repo
    :param repo_type: the type of SCM target repo
    :param pull_request: the pull request that was created
    :param data: extra data for specific events e.g {'comment': comment_obj}
    """
    if not _supports_repo_type(repo_type):
        return

    extras = _get_vcs_operation_context(username, repo_name, repo_type, 'create_pull_request')
    events.trigger(events.PullRequestCreateEvent(pull_request))
    extras.update(pull_request.get_api_data(with_merge_state=False))
    hooks_base.create_pull_request(**extras)


def trigger_merge_pull_request_hook(username, repo_name, repo_type, pull_request, data=None):
    """
    Triggers merge pull request action hooks

    :param username: username who creates the pull request
    :param repo_name: name of target repo
    :param repo_type: the type of SCM target repo
    :param pull_request: the pull request that was merged
    :param data: extra data for specific events e.g {'comment': comment_obj}
    """
    if not _supports_repo_type(repo_type):
        return

    extras = _get_vcs_operation_context(username, repo_name, repo_type, 'merge_pull_request')
    events.trigger(events.PullRequestMergeEvent(pull_request))
    extras.update(pull_request.get_api_data())
    hooks_base.merge_pull_request(**extras)


def trigger_close_pull_request_hook(username, repo_name, repo_type, pull_request, data=None):
    """
    Triggers close pull request action hooks

    :param username: username who creates the pull request
    :param repo_name: name of target repo
    :param repo_type: the type of SCM target repo
    :param pull_request: the pull request that was closed
    :param data: extra data for specific events e.g {'comment': comment_obj}
    """
    if not _supports_repo_type(repo_type):
        return

    extras = _get_vcs_operation_context(username, repo_name, repo_type, 'close_pull_request')
    events.trigger(events.PullRequestCloseEvent(pull_request))
    extras.update(pull_request.get_api_data())
    hooks_base.close_pull_request(**extras)


def trigger_review_pull_request_hook(username, repo_name, repo_type, pull_request, data=None):
    """
    Triggers review status change pull request action hooks

    :param username: username who creates the pull request
    :param repo_name: name of target repo
    :param repo_type: the type of SCM target repo
    :param pull_request: the pull request that review status changed
    :param data: extra data for specific events e.g {'comment': comment_obj}
    """
    if not _supports_repo_type(repo_type):
        return

    extras = _get_vcs_operation_context(username, repo_name, repo_type, 'review_pull_request')
    status = data.get('status')
    events.trigger(events.PullRequestReviewEvent(pull_request, status))
    extras.update(pull_request.get_api_data())
    hooks_base.review_pull_request(**extras)


def trigger_comment_pull_request_hook(username, repo_name, repo_type, pull_request, data=None):
    """
    Triggers when a comment is made on a pull request

    :param username: username who creates the pull request
    :param repo_name: name of target repo
    :param repo_type: the type of SCM target repo
    :param pull_request: the pull request that comment was made on
    :param data: extra data for specific events e.g {'comment': comment_obj}
    """
    if not _supports_repo_type(repo_type):
        return

    extras = _get_vcs_operation_context(username, repo_name, repo_type, 'comment_pull_request')

    comment = data['comment']
    events.trigger(events.PullRequestCommentEvent(pull_request, comment))
    extras.update(pull_request.get_api_data())
    extras.comment = comment.get_api_data()
    hooks_base.comment_pull_request(**extras)


def trigger_comment_pull_request_edit_hook(username, repo_name, repo_type, pull_request, data=None):
    """
    Triggers when a comment was edited on a pull request

    :param username: username who made the edit
    :param repo_name: name of target repo
    :param repo_type: the type of SCM target repo
    :param pull_request: the pull request that comment was made on
    :param data: extra data for specific events e.g {'comment': comment_obj}
    """
    if not _supports_repo_type(repo_type):
        return

    extras = _get_vcs_operation_context(username, repo_name, repo_type, 'comment_pull_request')

    comment = data['comment']
    events.trigger(events.PullRequestCommentEditEvent(pull_request, comment))
    extras.update(pull_request.get_api_data())
    extras.comment = comment.get_api_data()
    hooks_base.comment_edit_pull_request(**extras)


def trigger_update_pull_request_hook(username, repo_name, repo_type, pull_request, data=None):
    """
    Triggers update pull request action hooks

    :param username: username who creates the pull request
    :param repo_name: name of target repo
    :param repo_type: the type of SCM target repo
    :param pull_request: the pull request that was updated
    :param data: extra data for specific events e.g {'comment': comment_obj}
    """
    if not _supports_repo_type(repo_type):
        return

    extras = _get_vcs_operation_context(username, repo_name, repo_type, 'update_pull_request')
    events.trigger(events.PullRequestUpdateEvent(pull_request))
    extras.update(pull_request.get_api_data())
    hooks_base.update_pull_request(**extras)
