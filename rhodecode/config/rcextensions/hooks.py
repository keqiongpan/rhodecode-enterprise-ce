# Copyright (C) 2016-2019 RhodeCode GmbH
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
import logging
from .utils import DotDict, HookResponse, has_kwargs
log = logging.getLogger('rhodecode.' + __name__)


# Config shortcut to keep, all configuration in one place
# Example:  api_key = CONFIG.my_config.api_key
CONFIG = DotDict(
    my_config=DotDict(
        api_key='<secret>',
    ),

)


@has_kwargs({
    'repo_name': '',
    'repo_type': '',
    'description': '',
    'private': '',
    'created_on': '',
    'enable_downloads': '',
    'repo_id': '',
    'user_id': '',
    'enable_statistics': '',
    'clone_uri': '',
    'fork_id': '',
    'group_id': '',
    'created_by': ''
})
def _create_repo_hook(*args, **kwargs):
    """
    POST CREATE REPOSITORY HOOK. This function will be executed after
    each repository is created. kwargs available:

    """
    return HookResponse(0, '')


@has_kwargs({
    'group_name': '', 
    'group_parent_id': '', 
    'group_description': '',
    'group_id': '', 
    'user_id': '', 
    'created_by': '', 
    'created_on': '', 
    'enable_locking': ''
})
def _create_repo_group_hook(*args, **kwargs):
    """
    POST CREATE REPOSITORY GROUP HOOK, this function will be
    executed after each repository group is created. kwargs available:
    """
    return HookResponse(0, '')


@has_kwargs({
    'username': '', 
    'password': '', 
    'email': '', 
    'firstname': '',
    'lastname': '', 
    'active': '', 
    'admin': '', 
    'created_by': '',
})
def _pre_create_user_hook(*args, **kwargs):
    """
    PRE CREATE USER HOOK, this function will be executed before each
    user is created, it returns a tuple of bool, reason.
    If bool is False the user creation will be stopped and reason
    will be displayed to the user.

    Return HookResponse(1, reason) to block user creation

    """

    reason = 'allowed'
    return HookResponse(0, reason)


@has_kwargs({
    'username': '',
    'full_name_or_username': '',
    'full_contact': '',
    'user_id': '',
    'name': '',
    'firstname': '',
    'short_contact': '',
    'admin': '',
    'lastname': '',
    'ip_addresses': '',
    'extern_type': '',
    'extern_name': '',
    'email': '',
    'api_key': '',
    'api_keys': '',
    'last_login': '',
    'full_name': '',
    'active': '',
    'password': '',
    'emails': '',
    'inherit_default_permissions': '',
    'created_by': '',
    'created_on': '',
})
def _create_user_hook(*args, **kwargs):
    """
    POST CREATE USER HOOK, this function will be executed after each user is created
    """
    return HookResponse(0, '')


@has_kwargs({
    'repo_name': '',
    'repo_type': '',
    'description': '',
    'private': '',
    'created_on': '',
    'enable_downloads': '',
    'repo_id': '',
    'user_id': '',
    'enable_statistics': '',
    'clone_uri': '',
    'fork_id': '',
    'group_id': '',
    'deleted_by': '',
    'deleted_on': '',
})
def _delete_repo_hook(*args, **kwargs):
    """
    POST DELETE REPOSITORY HOOK, this function will be executed after
    each repository deletion
    """
    return HookResponse(0, '')


@has_kwargs({
    'username': '',
    'full_name_or_username': '',
    'full_contact': '',
    'user_id': '',
    'name': '',
    'short_contact': '',
    'admin': '',
    'firstname': '',
    'lastname': '',
    'ip_addresses': '',
    'email': '',
    'api_key': '',
    'last_login': '',
    'full_name': '',
    'active': '',
    'password': '',
    'emails': '',
    'inherit_default_permissions': '',
    'deleted_by': '',
 })
def _delete_user_hook(*args, **kwargs):
    """
    POST DELETE USER HOOK, this function will be executed after each
    user is deleted kwargs available:
    """
    return HookResponse(0, '')


# =============================================================================
# PUSH/PULL RELATED HOOKS
# =============================================================================
@has_kwargs({
    'server_url': 'url of instance that triggered this hook',
    'config': 'path to .ini config used',
    'scm': 'type of version control "git", "hg", "svn"',
    'username': 'username of actor who triggered this event',
    'ip': 'ip address of actor who triggered this hook',
    'action': '',
    'repository': 'repository name',
    'repo_store_path': 'full path to where repositories are stored',
    'commit_ids': 'pre transaction metadata for commit ids',
    'hook_type': '',
    'user_agent': 'Client user agent, e.g git or mercurial CLI version',
})
def _pre_push_hook(*args, **kwargs):
    """
    Post push hook
    To stop version control from storing the transaction and send a message to user
    use non-zero HookResponse with a message, e.g return HookResponse(1, 'Not allowed')

    This message will be shown back to client during PUSH operation

    Commit ids might look like that::

    [{u'hg_env|git_env': ...,
      u'multiple_heads': [],
      u'name': u'default',
      u'new_rev': u'd0befe0692e722e01d5677f27a104631cf798b69',
      u'old_rev': u'd0befe0692e722e01d5677f27a104631cf798b69',
      u'ref': u'',
      u'total_commits': 2,
      u'type': u'branch'}]
    """
    return HookResponse(0, '')


@has_kwargs({
    'server_url': 'url of instance that triggered this hook',
    'config': 'path to .ini config used',
    'scm': 'type of version control "git", "hg", "svn"',
    'username': 'username of actor who triggered this event',
    'ip': 'ip address of actor who triggered this hook',
    'action': '',
    'repository': 'repository name',
    'repo_store_path': 'full path to where repositories are stored',
    'commit_ids': 'list of pushed commit_ids (sha1)',
    'hook_type': '',
    'user_agent': 'Client user agent, e.g git or mercurial CLI version',
})
def _push_hook(*args, **kwargs):
    """
    POST PUSH HOOK, this function will be executed after each push it's
    executed after the build-in hook that RhodeCode uses for logging pushes
    """
    return HookResponse(0, '')


@has_kwargs({
    'server_url': 'url of instance that triggered this hook',
    'repo_store_path': 'full path to where repositories are stored',
    'config': 'path to .ini config used',
    'scm': 'type of version control "git", "hg", "svn"',
    'username': 'username of actor who triggered this event',
    'ip': 'ip address of actor who triggered this hook',
    'action': '',
    'repository': 'repository name',
    'hook_type': '',
    'user_agent': 'Client user agent, e.g git or mercurial CLI version',
})
def _pre_pull_hook(*args, **kwargs):
    """
    Post pull hook
    """
    return HookResponse(0, '')


@has_kwargs({
    'server_url': 'url of instance that triggered this hook',
    'repo_store_path': 'full path to where repositories are stored',
    'config': 'path to .ini config used',
    'scm': 'type of version control "git", "hg", "svn"',
    'username': 'username of actor who triggered this event',
    'ip': 'ip address of actor who triggered this hook',
    'action': '',
    'repository': 'repository name',
    'hook_type': '',
    'user_agent': 'Client user agent, e.g git or mercurial CLI version',
})
def _pull_hook(*args, **kwargs):
    """
    This hook will be executed after each code pull.
    """
    return HookResponse(0, '')


# =============================================================================
#  PULL REQUEST RELATED HOOKS
# =============================================================================
@has_kwargs({
    'server_url': 'url of instance that triggered this hook',
    'config': 'path to .ini config used',
    'scm': 'type of version control "git", "hg", "svn"',
    'username': 'username of actor who triggered this event',
    'ip': 'ip address of actor who triggered this hook',
    'action': '',
    'repository': 'repository name',
    'pull_request_id': '',
    'url': '',
    'title': '',
    'description': '',
    'status': '',
    'created_on': '',
    'updated_on': '',
    'commit_ids': '',
    'review_status': '',
    'mergeable': '',
    'source': '',
    'target': '',
    'author': '',
    'reviewers': '',
})
def _create_pull_request_hook(*args, **kwargs):
    """
    This hook will be executed after creation of a pull request.
    """
    return HookResponse(0, '')


@has_kwargs({
    'server_url': 'url of instance that triggered this hook',
    'config': 'path to .ini config used',
    'scm': 'type of version control "git", "hg", "svn"',
    'username': 'username of actor who triggered this event',
    'ip': 'ip address of actor who triggered this hook',
    'action': '',
    'repository': 'repository name',
    'pull_request_id': '',
    'url': '',
    'title': '',
    'description': '',
    'status': '',
    'created_on': '',
    'updated_on': '',
    'commit_ids': '',
    'review_status': '',
    'mergeable': '',
    'source': '',
    'target': '',
    'author': '',
    'reviewers': '',
})
def _review_pull_request_hook(*args, **kwargs):
    """
    This hook will be executed after review action was made on a pull request.
    """
    return HookResponse(0, '')


@has_kwargs({
    'server_url': 'url of instance that triggered this hook',
    'config': 'path to .ini config used',
    'scm': 'type of version control "git", "hg", "svn"',
    'username': 'username of actor who triggered this event',
    'ip': 'ip address of actor who triggered this hook',
    'action': '',
    'repository': 'repository name',
    'pull_request_id': '',
    'url': '',
    'title': '',
    'description': '',
    'status': '',
    'created_on': '',
    'updated_on': '',
    'commit_ids': '',
    'review_status': '',
    'mergeable': '',
    'source': '',
    'target': '',
    'author': '',
    'reviewers': '',
})
def _update_pull_request_hook(*args, **kwargs):
    """
    This hook will be executed after pull requests has been updated with new commits.
    """
    return HookResponse(0, '')


@has_kwargs({
    'server_url': 'url of instance that triggered this hook',
    'config': 'path to .ini config used',
    'scm': 'type of version control "git", "hg", "svn"',
    'username': 'username of actor who triggered this event',
    'ip': 'ip address of actor who triggered this hook',
    'action': '',
    'repository': 'repository name',
    'pull_request_id': '',
    'url': '',
    'title': '',
    'description': '',
    'status': '',
    'created_on': '',
    'updated_on': '',
    'commit_ids': '',
    'review_status': '',
    'mergeable': '',
    'source': '',
    'target': '',
    'author': '',
    'reviewers': '',
})
def _merge_pull_request_hook(*args, **kwargs):
    """
    This hook will be executed after merge of a pull request.
    """
    return HookResponse(0, '')


@has_kwargs({
    'server_url': 'url of instance that triggered this hook',
    'config': 'path to .ini config used',
    'scm': 'type of version control "git", "hg", "svn"',
    'username': 'username of actor who triggered this event',
    'ip': 'ip address of actor who triggered this hook',
    'action': '',
    'repository': 'repository name',
    'pull_request_id': '',
    'url': '',
    'title': '',
    'description': '',
    'status': '',
    'created_on': '',
    'updated_on': '',
    'commit_ids': '',
    'review_status': '',
    'mergeable': '',
    'source': '',
    'target': '',
    'author': '',
    'reviewers': '',
})
def _close_pull_request_hook(*args, **kwargs):
    """
    This hook will be executed after close of a pull request.
    """
    return HookResponse(0, '')
