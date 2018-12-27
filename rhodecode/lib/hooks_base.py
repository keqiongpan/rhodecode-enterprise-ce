# -*- coding: utf-8 -*-

# Copyright (C) 2013-2018 RhodeCode GmbH
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
Set of hooks run by RhodeCode Enterprise
"""

import os
import collections
import logging

import rhodecode
from rhodecode import events
from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.utils2 import safe_str
from rhodecode.lib.exceptions import (
    HTTPLockedRC, HTTPBranchProtected, UserCreationError)
from rhodecode.model.db import Repository, User

log = logging.getLogger(__name__)


class HookResponse(object):
    def __init__(self, status, output):
        self.status = status
        self.output = output

    def __add__(self, other):
        other_status = getattr(other, 'status', 0)
        new_status = max(self.status, other_status)
        other_output = getattr(other, 'output', '')
        new_output = self.output + other_output

        return HookResponse(new_status, new_output)

    def __bool__(self):
        return self.status == 0


def is_shadow_repo(extras):
    """
    Returns ``True`` if this is an action executed against a shadow repository.
    """
    return extras['is_shadow_repo']


def _get_scm_size(alias, root_path):

    if not alias.startswith('.'):
        alias += '.'

    size_scm, size_root = 0, 0
    for path, unused_dirs, files in os.walk(safe_str(root_path)):
        if path.find(alias) != -1:
            for f in files:
                try:
                    size_scm += os.path.getsize(os.path.join(path, f))
                except OSError:
                    pass
        else:
            for f in files:
                try:
                    size_root += os.path.getsize(os.path.join(path, f))
                except OSError:
                    pass

    size_scm_f = h.format_byte_size_binary(size_scm)
    size_root_f = h.format_byte_size_binary(size_root)
    size_total_f = h.format_byte_size_binary(size_root + size_scm)

    return size_scm_f, size_root_f, size_total_f


# actual hooks called by Mercurial internally, and GIT by our Python Hooks
def repo_size(extras):
    """Present size of repository after push."""
    repo = Repository.get_by_repo_name(extras.repository)
    vcs_part = safe_str(u'.%s' % repo.repo_type)
    size_vcs, size_root, size_total = _get_scm_size(vcs_part,
                                                    repo.repo_full_path)
    msg = ('Repository `%s` size summary %s:%s repo:%s total:%s\n'
           % (repo.repo_name, vcs_part, size_vcs, size_root, size_total))
    return HookResponse(0, msg)


def pre_push(extras):
    """
    Hook executed before pushing code.

    It bans pushing when the repository is locked.
    """

    user = User.get_by_username(extras.username)
    output = ''
    if extras.locked_by[0] and user.user_id != int(extras.locked_by[0]):
        locked_by = User.get(extras.locked_by[0]).username
        reason = extras.locked_by[2]
        # this exception is interpreted in git/hg middlewares and based
        # on that proper return code is server to client
        _http_ret = HTTPLockedRC(
            _locked_by_explanation(extras.repository, locked_by, reason))
        if str(_http_ret.code).startswith('2'):
            # 2xx Codes don't raise exceptions
            output = _http_ret.title
        else:
            raise _http_ret

    hook_response = ''
    if not is_shadow_repo(extras):
        if extras.commit_ids and extras.check_branch_perms:

            auth_user = user.AuthUser()
            repo = Repository.get_by_repo_name(extras.repository)
            affected_branches = []
            if repo.repo_type == 'hg':
                for entry in extras.commit_ids:
                    if entry['type'] == 'branch':
                        is_forced = bool(entry['multiple_heads'])
                        affected_branches.append([entry['name'], is_forced])
            elif repo.repo_type == 'git':
                for entry in extras.commit_ids:
                    if entry['type'] == 'heads':
                        is_forced = bool(entry['pruned_sha'])
                        affected_branches.append([entry['name'], is_forced])

            for branch_name, is_forced in affected_branches:

                rule, branch_perm = auth_user.get_rule_and_branch_permission(
                    extras.repository, branch_name)
                if not branch_perm:
                    # no branch permission found for this branch, just keep checking
                    continue

                if branch_perm == 'branch.push_force':
                    continue
                elif branch_perm == 'branch.push' and is_forced is False:
                    continue
                elif branch_perm == 'branch.push' and is_forced is True:
                    halt_message = 'Branch `{}` changes rejected by rule {}. ' \
                                   'FORCE PUSH FORBIDDEN.'.format(branch_name, rule)
                else:
                    halt_message = 'Branch `{}` changes rejected by rule {}.'.format(
                        branch_name, rule)

                if halt_message:
                    _http_ret = HTTPBranchProtected(halt_message)
                    raise _http_ret

        # Propagate to external components. This is done after checking the
        # lock, for consistent behavior.
        hook_response = pre_push_extension(
            repo_store_path=Repository.base_path(), **extras)
        events.trigger(events.RepoPrePushEvent(
            repo_name=extras.repository, extras=extras))

    return HookResponse(0, output) + hook_response


def pre_pull(extras):
    """
    Hook executed before pulling the code.

    It bans pulling when the repository is locked.
    """

    output = ''
    if extras.locked_by[0]:
        locked_by = User.get(extras.locked_by[0]).username
        reason = extras.locked_by[2]
        # this exception is interpreted in git/hg middlewares and based
        # on that proper return code is server to client
        _http_ret = HTTPLockedRC(
            _locked_by_explanation(extras.repository, locked_by, reason))
        if str(_http_ret.code).startswith('2'):
            # 2xx Codes don't raise exceptions
            output = _http_ret.title
        else:
            raise _http_ret

    # Propagate to external components. This is done after checking the
    # lock, for consistent behavior.
    hook_response = ''
    if not is_shadow_repo(extras):
        extras.hook_type = extras.hook_type or 'pre_pull'
        hook_response = pre_pull_extension(
            repo_store_path=Repository.base_path(), **extras)
        events.trigger(events.RepoPrePullEvent(
            repo_name=extras.repository, extras=extras))

    return HookResponse(0, output) + hook_response


def post_pull(extras):
    """Hook executed after client pulls the code."""

    audit_user = audit_logger.UserWrap(
        username=extras.username,
        ip_addr=extras.ip)
    repo = audit_logger.RepoWrap(repo_name=extras.repository)
    audit_logger.store(
        'user.pull', action_data={'user_agent': extras.user_agent},
        user=audit_user, repo=repo, commit=True)

    output = ''
    # make lock is a tri state False, True, None. We only make lock on True
    if extras.make_lock is True and not is_shadow_repo(extras):
        user = User.get_by_username(extras.username)
        Repository.lock(Repository.get_by_repo_name(extras.repository),
                        user.user_id,
                        lock_reason=Repository.LOCK_PULL)
        msg = 'Made lock on repo `%s`' % (extras.repository,)
        output += msg

    if extras.locked_by[0]:
        locked_by = User.get(extras.locked_by[0]).username
        reason = extras.locked_by[2]
        _http_ret = HTTPLockedRC(
            _locked_by_explanation(extras.repository, locked_by, reason))
        if str(_http_ret.code).startswith('2'):
            # 2xx Codes don't raise exceptions
            output += _http_ret.title

    # Propagate to external components.
    hook_response = ''
    if not is_shadow_repo(extras):
        extras.hook_type = extras.hook_type or 'post_pull'
        hook_response = post_pull_extension(
            repo_store_path=Repository.base_path(), **extras)
        events.trigger(events.RepoPullEvent(
            repo_name=extras.repository, extras=extras))

    return HookResponse(0, output) + hook_response


def post_push(extras):
    """Hook executed after user pushes to the repository."""
    commit_ids = extras.commit_ids

    # log the push call
    audit_user = audit_logger.UserWrap(
        username=extras.username, ip_addr=extras.ip)
    repo = audit_logger.RepoWrap(repo_name=extras.repository)
    audit_logger.store(
        'user.push', action_data={
            'user_agent': extras.user_agent,
            'commit_ids': commit_ids[:400]},
        user=audit_user, repo=repo, commit=True)

    # Propagate to external components.
    output = ''
    # make lock is a tri state False, True, None. We only release lock on False
    if extras.make_lock is False and not is_shadow_repo(extras):
        Repository.unlock(Repository.get_by_repo_name(extras.repository))
        msg = 'Released lock on repo `%s`\n' % extras.repository
        output += msg

    if extras.locked_by[0]:
        locked_by = User.get(extras.locked_by[0]).username
        reason = extras.locked_by[2]
        _http_ret = HTTPLockedRC(
            _locked_by_explanation(extras.repository, locked_by, reason))
        # TODO: johbo: if not?
        if str(_http_ret.code).startswith('2'):
            # 2xx Codes don't raise exceptions
            output += _http_ret.title

    if extras.new_refs:
        tmpl = extras.server_url + '/' + extras.repository + \
               "/pull-request/new?{ref_type}={ref_name}"

        for branch_name in extras.new_refs['branches']:
            output += 'RhodeCode: open pull request link: {}\n'.format(
                tmpl.format(ref_type='branch', ref_name=safe_str(branch_name)))

        for book_name in extras.new_refs['bookmarks']:
            output += 'RhodeCode: open pull request link: {}\n'.format(
                tmpl.format(ref_type='bookmark', ref_name=safe_str(book_name)))

    hook_response = ''
    if not is_shadow_repo(extras):
        hook_response = post_push_extension(
            repo_store_path=Repository.base_path(),
            **extras)
        events.trigger(events.RepoPushEvent(
            repo_name=extras.repository, pushed_commit_ids=commit_ids, extras=extras))

    output += 'RhodeCode: push completed\n'
    return HookResponse(0, output) + hook_response


def _locked_by_explanation(repo_name, user_name, reason):
    message = (
        'Repository `%s` locked by user `%s`. Reason:`%s`'
        % (repo_name, user_name, reason))
    return message


def check_allowed_create_user(user_dict, created_by, **kwargs):
    # pre create hooks
    if pre_create_user.is_active():
        hook_result = pre_create_user(created_by=created_by, **user_dict)
        allowed = hook_result.status == 0
        if not allowed:
            reason = hook_result.output
            raise UserCreationError(reason)


class ExtensionCallback(object):
    """
    Forwards a given call to rcextensions, sanitizes keyword arguments.

    Does check if there is an extension active for that hook. If it is
    there, it will forward all `kwargs_keys` keyword arguments to the
    extension callback.
    """

    def __init__(self, hook_name, kwargs_keys):
        self._hook_name = hook_name
        self._kwargs_keys = set(kwargs_keys)

    def __call__(self, *args, **kwargs):
        log.debug('Calling extension callback for `%s`', self._hook_name)
        callback = self._get_callback()
        if not callback:
            log.debug('extension callback `%s` not found, skipping...', self._hook_name)
            return

        kwargs_to_pass = {}
        for key in self._kwargs_keys:
            try:
                kwargs_to_pass[key] = kwargs[key]
            except KeyError:
                log.error('Failed to fetch %s key. Expected keys: %s',
                          key, self._kwargs_keys)
                raise

        # backward compat for removed api_key for old hooks. This was it works
        # with older rcextensions that require api_key present
        if self._hook_name in ['CREATE_USER_HOOK', 'DELETE_USER_HOOK']:
            kwargs_to_pass['api_key'] = '_DEPRECATED_'
        return callback(**kwargs_to_pass)

    def is_active(self):
        return hasattr(rhodecode.EXTENSIONS, self._hook_name)

    def _get_callback(self):
        return getattr(rhodecode.EXTENSIONS, self._hook_name, None)


pre_pull_extension = ExtensionCallback(
    hook_name='PRE_PULL_HOOK',
    kwargs_keys=(
        'server_url', 'config', 'scm', 'username', 'ip', 'action',
        'repository', 'hook_type', 'user_agent', 'repo_store_path',))


post_pull_extension = ExtensionCallback(
    hook_name='PULL_HOOK',
    kwargs_keys=(
        'server_url', 'config', 'scm', 'username', 'ip', 'action',
        'repository', 'hook_type', 'user_agent', 'repo_store_path',))


pre_push_extension = ExtensionCallback(
    hook_name='PRE_PUSH_HOOK',
    kwargs_keys=(
        'server_url', 'config', 'scm', 'username', 'ip', 'action',
        'repository', 'repo_store_path', 'commit_ids', 'hook_type', 'user_agent',))


post_push_extension = ExtensionCallback(
    hook_name='PUSH_HOOK',
    kwargs_keys=(
        'server_url', 'config', 'scm', 'username', 'ip', 'action',
        'repository', 'repo_store_path', 'commit_ids', 'hook_type', 'user_agent',))


pre_create_user = ExtensionCallback(
    hook_name='PRE_CREATE_USER_HOOK',
    kwargs_keys=(
        'username', 'password', 'email', 'firstname', 'lastname', 'active',
        'admin', 'created_by'))


log_create_pull_request = ExtensionCallback(
    hook_name='CREATE_PULL_REQUEST',
    kwargs_keys=(
        'server_url', 'config', 'scm', 'username', 'ip', 'action',
        'repository', 'pull_request_id', 'url', 'title', 'description',
        'status', 'created_on', 'updated_on', 'commit_ids', 'review_status',
        'mergeable', 'source', 'target', 'author', 'reviewers'))


log_merge_pull_request = ExtensionCallback(
    hook_name='MERGE_PULL_REQUEST',
    kwargs_keys=(
        'server_url', 'config', 'scm', 'username', 'ip', 'action',
        'repository', 'pull_request_id', 'url', 'title', 'description',
        'status', 'created_on', 'updated_on', 'commit_ids', 'review_status',
        'mergeable', 'source', 'target', 'author', 'reviewers'))


log_close_pull_request = ExtensionCallback(
    hook_name='CLOSE_PULL_REQUEST',
    kwargs_keys=(
        'server_url', 'config', 'scm', 'username', 'ip', 'action',
        'repository', 'pull_request_id', 'url', 'title', 'description',
        'status', 'created_on', 'updated_on', 'commit_ids', 'review_status',
        'mergeable', 'source', 'target', 'author', 'reviewers'))


log_review_pull_request = ExtensionCallback(
    hook_name='REVIEW_PULL_REQUEST',
    kwargs_keys=(
        'server_url', 'config', 'scm', 'username', 'ip', 'action',
        'repository', 'pull_request_id', 'url', 'title', 'description',
        'status', 'created_on', 'updated_on', 'commit_ids', 'review_status',
        'mergeable', 'source', 'target', 'author', 'reviewers'))


log_update_pull_request = ExtensionCallback(
    hook_name='UPDATE_PULL_REQUEST',
    kwargs_keys=(
        'server_url', 'config', 'scm', 'username', 'ip', 'action',
        'repository', 'pull_request_id', 'url', 'title', 'description',
        'status', 'created_on', 'updated_on', 'commit_ids', 'review_status',
        'mergeable', 'source', 'target', 'author', 'reviewers'))


log_create_user = ExtensionCallback(
    hook_name='CREATE_USER_HOOK',
    kwargs_keys=(
        'username', 'full_name_or_username', 'full_contact', 'user_id',
        'name', 'firstname', 'short_contact', 'admin', 'lastname',
        'ip_addresses', 'extern_type', 'extern_name',
        'email', 'api_keys', 'last_login',
        'full_name', 'active', 'password', 'emails',
        'inherit_default_permissions', 'created_by', 'created_on'))


log_delete_user = ExtensionCallback(
    hook_name='DELETE_USER_HOOK',
    kwargs_keys=(
        'username', 'full_name_or_username', 'full_contact', 'user_id',
        'name', 'firstname', 'short_contact', 'admin', 'lastname',
        'ip_addresses',
        'email', 'last_login',
        'full_name', 'active', 'password', 'emails',
        'inherit_default_permissions', 'deleted_by'))


log_create_repository = ExtensionCallback(
    hook_name='CREATE_REPO_HOOK',
    kwargs_keys=(
        'repo_name', 'repo_type', 'description', 'private', 'created_on',
        'enable_downloads', 'repo_id', 'user_id', 'enable_statistics',
        'clone_uri', 'fork_id', 'group_id', 'created_by'))


log_delete_repository = ExtensionCallback(
    hook_name='DELETE_REPO_HOOK',
    kwargs_keys=(
        'repo_name', 'repo_type', 'description', 'private', 'created_on',
        'enable_downloads', 'repo_id', 'user_id', 'enable_statistics',
        'clone_uri', 'fork_id', 'group_id', 'deleted_by', 'deleted_on'))


log_create_repository_group = ExtensionCallback(
    hook_name='CREATE_REPO_GROUP_HOOK',
    kwargs_keys=(
        'group_name', 'group_parent_id', 'group_description',
        'group_id', 'user_id', 'created_by', 'created_on',
        'enable_locking'))
