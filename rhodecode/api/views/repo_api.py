# -*- coding: utf-8 -*-

# Copyright (C) 2011-2020 RhodeCode GmbH
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
import time

import rhodecode
from rhodecode.api import (
    jsonrpc_method, JSONRPCError, JSONRPCForbidden, JSONRPCValidationError)
from rhodecode.api.utils import (
    has_superadmin_permission, Optional, OAttr, get_repo_or_error,
    get_user_group_or_error, get_user_or_error, validate_repo_permissions,
    get_perm_or_error, parse_args, get_origin, build_commit_data,
    validate_set_owner_permissions)
from rhodecode.lib import audit_logger, rc_cache, channelstream
from rhodecode.lib import repo_maintenance
from rhodecode.lib.auth import (
    HasPermissionAnyApi, HasUserGroupPermissionAnyApi,
    HasRepoPermissionAnyApi)
from rhodecode.lib.celerylib.utils import get_task_id
from rhodecode.lib.utils2 import (
    str2bool, time_to_datetime, safe_str, safe_int, safe_unicode)
from rhodecode.lib.ext_json import json
from rhodecode.lib.exceptions import (
    StatusChangeOnClosedPullRequestError, CommentVersionMismatch)
from rhodecode.lib.vcs import RepositoryError
from rhodecode.lib.vcs.exceptions import NodeDoesNotExistError
from rhodecode.model.changeset_status import ChangesetStatusModel
from rhodecode.model.comment import CommentsModel
from rhodecode.model.db import (
    Session, ChangesetStatus, RepositoryField, Repository, RepoGroup,
    ChangesetComment)
from rhodecode.model.permission import PermissionModel
from rhodecode.model.pull_request import PullRequestModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.scm import ScmModel, RepoList
from rhodecode.model.settings import SettingsModel, VcsSettingsModel
from rhodecode.model import validation_schema
from rhodecode.model.validation_schema.schemas import repo_schema

log = logging.getLogger(__name__)


@jsonrpc_method()
def get_repo(request, apiuser, repoid, cache=Optional(True)):
    """
    Gets an existing repository by its name or repository_id.

    The members section so the output returns users groups or users
    associated with that repository.

    This command can only be run using an |authtoken| with admin rights,
    or users with at least read rights to the |repo|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: The repository name or repository id.
    :type repoid: str or int
    :param cache: use the cached value for last changeset
    :type: cache: Optional(bool)

    Example output:

    .. code-block:: bash

        {
          "error": null,
          "id": <repo_id>,
          "result": {
            "clone_uri": null,
            "created_on": "timestamp",
            "description": "repo description",
            "enable_downloads": false,
            "enable_locking": false,
            "enable_statistics": false,
            "followers": [
              {
                "active": true,
                "admin": false,
                "api_key": "****************************************",
                "api_keys": [
                  "****************************************"
                ],
                "email": "user@example.com",
                "emails": [
                  "user@example.com"
                ],
                "extern_name": "rhodecode",
                "extern_type": "rhodecode",
                "firstname": "username",
                "ip_addresses": [],
                "language": null,
                "last_login": "2015-09-16T17:16:35.854",
                "lastname": "surname",
                "user_id": <user_id>,
                "username": "name"
              }
            ],
            "fork_of": "parent-repo",
            "landing_rev": [
              "rev",
              "tip"
            ],
            "last_changeset": {
              "author": "User <user@example.com>",
              "branch": "default",
              "date": "timestamp",
              "message": "last commit message",
              "parents": [
                {
                  "raw_id": "commit-id"
                }
              ],
              "raw_id": "commit-id",
              "revision": <revision number>,
              "short_id": "short id"
            },
            "lock_reason": null,
            "locked_by": null,
            "locked_date": null,
            "owner": "owner-name",
            "permissions": [
              {
                "name": "super-admin-name",
                "origin": "super-admin",
                "permission": "repository.admin",
                "type": "user"
              },
              {
                "name": "owner-name",
                "origin": "owner",
                "permission": "repository.admin",
                "type": "user"
              },
              {
                "name": "user-group-name",
                "origin": "permission",
                "permission": "repository.write",
                "type": "user_group"
              }
            ],
            "private": true,
            "repo_id": 676,
            "repo_name": "user-group/repo-name",
            "repo_type": "hg"
          }
        }
    """

    repo = get_repo_or_error(repoid)
    cache = Optional.extract(cache)

    include_secrets = False
    if has_superadmin_permission(apiuser):
        include_secrets = True
    else:
        # check if we have at least read permission for this repo !
        _perms = (
            'repository.admin', 'repository.write', 'repository.read',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    permissions = []
    for _user in repo.permissions():
        user_data = {
            'name': _user.username,
            'permission': _user.permission,
            'origin': get_origin(_user),
            'type': "user",
        }
        permissions.append(user_data)

    for _user_group in repo.permission_user_groups():
        user_group_data = {
            'name': _user_group.users_group_name,
            'permission': _user_group.permission,
            'origin': get_origin(_user_group),
            'type': "user_group",
        }
        permissions.append(user_group_data)

    following_users = [
        user.user.get_api_data(include_secrets=include_secrets)
        for user in repo.followers]

    if not cache:
        repo.update_commit_cache()
    data = repo.get_api_data(include_secrets=include_secrets)
    data['permissions'] = permissions
    data['followers'] = following_users
    return data


@jsonrpc_method()
def get_repos(request, apiuser, root=Optional(None), traverse=Optional(True)):
    """
    Lists all existing repositories.

    This command can only be run using an |authtoken| with admin rights,
    or users with at least read rights to |repos|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param root: specify root repository group to fetch repositories.
        filters the returned repositories to be members of given root group.
    :type root: Optional(None)
    :param traverse: traverse given root into subrepositories. With this flag
        set to False, it will only return top-level repositories from `root`.
        if root is empty it will return just top-level repositories.
    :type traverse: Optional(True)


    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result: [
                  {
                    "repo_id" :          "<repo_id>",
                    "repo_name" :        "<reponame>"
                    "repo_type" :        "<repo_type>",
                    "clone_uri" :        "<clone_uri>",
                    "private": :         "<bool>",
                    "created_on" :       "<datetimecreated>",
                    "description" :      "<description>",
                    "landing_rev":       "<landing_rev>",
                    "owner":             "<repo_owner>",
                    "fork_of":           "<name_of_fork_parent>",
                    "enable_downloads":  "<bool>",
                    "enable_locking":    "<bool>",
                    "enable_statistics": "<bool>",
                  },
                  ...
                ]
        error:  null
    """

    include_secrets = has_superadmin_permission(apiuser)
    _perms = ('repository.read', 'repository.write', 'repository.admin',)
    extras = {'user': apiuser}

    root = Optional.extract(root)
    traverse = Optional.extract(traverse, binary=True)

    if root:
        # verify parent existance, if it's empty return an error
        parent = RepoGroup.get_by_group_name(root)
        if not parent:
            raise JSONRPCError(
                'Root repository group `{}` does not exist'.format(root))

        if traverse:
            repos = RepoModel().get_repos_for_root(root=root, traverse=traverse)
        else:
            repos = RepoModel().get_repos_for_root(root=parent)
    else:
        if traverse:
            repos = RepoModel().get_all()
        else:
            # return just top-level
            repos = RepoModel().get_repos_for_root(root=None)

    repo_list = RepoList(repos, perm_set=_perms, extra_kwargs=extras)
    return [repo.get_api_data(include_secrets=include_secrets)
            for repo in repo_list]


@jsonrpc_method()
def get_repo_changeset(request, apiuser, repoid, revision,
                       details=Optional('basic')):
    """
    Returns information about a changeset.

    Additionally parameters define the amount of details returned by
    this function.

    This command can only be run using an |authtoken| with admin rights,
    or users with at least read rights to the |repo|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: The repository name or repository id
    :type repoid: str or int
    :param revision: revision for which listing should be done
    :type revision: str
    :param details: details can be 'basic|extended|full' full gives diff
        info details like the diff itself, and number of changed files etc.
    :type details: Optional(str)

    """
    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin', 'repository.write', 'repository.read',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    changes_details = Optional.extract(details)
    _changes_details_types = ['basic', 'extended', 'full']
    if changes_details not in _changes_details_types:
        raise JSONRPCError(
            'ret_type must be one of %s' % (
                ','.join(_changes_details_types)))

    vcs_repo = repo.scm_instance()
    pre_load = ['author', 'branch', 'date', 'message', 'parents',
                'status', '_commit', '_file_paths']

    try:
        commit = repo.get_commit(commit_id=revision, pre_load=pre_load)
    except TypeError as e:
        raise JSONRPCError(safe_str(e))
    _cs_json = commit.__json__()
    _cs_json['diff'] = build_commit_data(vcs_repo, commit, changes_details)
    if changes_details == 'full':
        _cs_json['refs'] = commit._get_refs()
    return _cs_json


@jsonrpc_method()
def get_repo_changesets(request, apiuser, repoid, start_rev, limit,
                        details=Optional('basic')):
    """
    Returns a set of commits limited by the number starting
    from the `start_rev` option.

    Additional parameters define the amount of details returned by this
    function.

    This command can only be run using an |authtoken| with admin rights,
    or users with at least read rights to |repos|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: The repository name or repository ID.
    :type repoid: str or int
    :param start_rev: The starting revision from where to get changesets.
    :type start_rev: str
    :param limit: Limit the number of commits to this amount
    :type limit: str or int
    :param details: Set the level of detail returned. Valid option are:
        ``basic``, ``extended`` and ``full``.
    :type details: Optional(str)

    .. note::

       Setting the parameter `details` to the value ``full`` is extensive
       and returns details like the diff itself, and the number
       of changed files.

    """
    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin', 'repository.write', 'repository.read',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    changes_details = Optional.extract(details)
    _changes_details_types = ['basic', 'extended', 'full']
    if changes_details not in _changes_details_types:
        raise JSONRPCError(
            'ret_type must be one of %s' % (
                ','.join(_changes_details_types)))

    limit = int(limit)
    pre_load = ['author', 'branch', 'date', 'message', 'parents',
                'status', '_commit', '_file_paths']

    vcs_repo = repo.scm_instance()
    # SVN needs a special case to distinguish its index and commit id
    if vcs_repo and vcs_repo.alias == 'svn' and (start_rev == '0'):
        start_rev = vcs_repo.commit_ids[0]

    try:
        commits = vcs_repo.get_commits(
            start_id=start_rev, pre_load=pre_load, translate_tags=False)
    except TypeError as e:
        raise JSONRPCError(safe_str(e))
    except Exception:
        log.exception('Fetching of commits failed')
        raise JSONRPCError('Error occurred during commit fetching')

    ret = []
    for cnt, commit in enumerate(commits):
        if cnt >= limit != -1:
            break
        _cs_json = commit.__json__()
        _cs_json['diff'] = build_commit_data(vcs_repo, commit, changes_details)
        if changes_details == 'full':
            _cs_json['refs'] = {
                'branches': [commit.branch],
                'bookmarks': getattr(commit, 'bookmarks', []),
                'tags': commit.tags
            }
        ret.append(_cs_json)
    return ret


@jsonrpc_method()
def get_repo_nodes(request, apiuser, repoid, revision, root_path,
                   ret_type=Optional('all'), details=Optional('basic'),
                   max_file_bytes=Optional(None)):
    """
    Returns a list of nodes and children in a flat list for a given
    path at given revision.

    It's possible to specify ret_type to show only `files` or `dirs`.

    This command can only be run using an |authtoken| with admin rights,
    or users with at least read rights to |repos|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: The repository name or repository ID.
    :type repoid: str or int
    :param revision: The revision for which listing should be done.
    :type revision: str
    :param root_path: The path from which to start displaying.
    :type root_path: str
    :param ret_type: Set the return type. Valid options are
        ``all`` (default), ``files`` and ``dirs``.
    :type ret_type: Optional(str)
    :param details: Returns extended information about nodes, such as
        md5, binary, and or content.
        The valid options are ``basic`` and ``full``.
    :type details: Optional(str)
    :param max_file_bytes: Only return file content under this file size bytes
    :type details: Optional(int)

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result: [
                    {
                      "binary": false,
                      "content": "File line",
                      "extension": "md",
                      "lines": 2,
                      "md5": "059fa5d29b19c0657e384749480f6422",
                      "mimetype": "text/x-minidsrc",
                      "name": "file.md",
                      "size": 580,
                      "type": "file"
                    },
                  ...
                ]
        error:  null
    """

    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin', 'repository.write', 'repository.read',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    ret_type = Optional.extract(ret_type)
    details = Optional.extract(details)
    _extended_types = ['basic', 'full']
    if details not in _extended_types:
        raise JSONRPCError('ret_type must be one of %s' % (','.join(_extended_types)))
    extended_info = False
    content = False
    if details == 'basic':
        extended_info = True

    if details == 'full':
        extended_info = content = True

    _map = {}
    try:
        # check if repo is not empty by any chance, skip quicker if it is.
        _scm = repo.scm_instance()
        if _scm.is_empty():
            return []

        _d, _f = ScmModel().get_nodes(
            repo, revision, root_path, flat=False,
            extended_info=extended_info, content=content,
            max_file_bytes=max_file_bytes)
        _map = {
            'all': _d + _f,
            'files': _f,
            'dirs': _d,
        }
        return _map[ret_type]
    except KeyError:
        raise JSONRPCError(
            'ret_type must be one of %s' % (','.join(sorted(_map.keys()))))
    except Exception:
        log.exception("Exception occurred while trying to get repo nodes")
        raise JSONRPCError(
            'failed to get repo: `%s` nodes' % repo.repo_name
        )


@jsonrpc_method()
def get_repo_file(request, apiuser, repoid, commit_id, file_path,
                  max_file_bytes=Optional(None), details=Optional('basic'),
                  cache=Optional(True)):
    """
    Returns a single file from repository at given revision.

    This command can only be run using an |authtoken| with admin rights,
    or users with at least read rights to |repos|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: The repository name or repository ID.
    :type repoid: str or int
    :param commit_id: The revision for which listing should be done.
    :type commit_id: str
    :param file_path: The path from which to start displaying.
    :type file_path: str
    :param details: Returns different set of information about nodes.
        The valid options are ``minimal`` ``basic`` and ``full``.
    :type details: Optional(str)
    :param max_file_bytes: Only return file content under this file size bytes
    :type max_file_bytes: Optional(int)
    :param cache: Use internal caches for fetching files. If disabled fetching
        files is slower but more memory efficient
    :type cache: Optional(bool)

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result: {
            "binary": false,
            "extension": "py",
            "lines": 35,
            "content": "....",
            "md5": "76318336366b0f17ee249e11b0c99c41",
            "mimetype": "text/x-python",
            "name": "python.py",
            "size": 817,
            "type": "file",
        }
        error:  null
    """

    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin', 'repository.write', 'repository.read',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    cache = Optional.extract(cache, binary=True)
    details = Optional.extract(details)
    _extended_types = ['minimal', 'minimal+search', 'basic', 'full']
    if details not in _extended_types:
        raise JSONRPCError(
            'ret_type must be one of %s, got %s' % (','.join(_extended_types)), details)
    extended_info = False
    content = False

    if details == 'minimal':
        extended_info = False

    elif details == 'basic':
        extended_info = True

    elif details == 'full':
        extended_info = content = True

    file_path = safe_unicode(file_path)
    try:
        # check if repo is not empty by any chance, skip quicker if it is.
        _scm = repo.scm_instance()
        if _scm.is_empty():
            return None

        node = ScmModel().get_node(
            repo, commit_id, file_path, extended_info=extended_info,
            content=content, max_file_bytes=max_file_bytes, cache=cache)
    except NodeDoesNotExistError:
        raise JSONRPCError(u'There is no file in repo: `{}` at path `{}` for commit: `{}`'.format(
            repo.repo_name, file_path, commit_id))
    except Exception:
        log.exception(u"Exception occurred while trying to get repo %s file",
                      repo.repo_name)
        raise JSONRPCError(u'failed to get repo: `{}` file at path {}'.format(
            repo.repo_name, file_path))

    return node


@jsonrpc_method()
def get_repo_fts_tree(request, apiuser, repoid, commit_id, root_path):
    """
    Returns a list of tree nodes for path at given revision. This api is built
    strictly for usage in full text search building, and shouldn't be consumed

    This command can only be run using an |authtoken| with admin rights,
    or users with at least read rights to |repos|.

    """

    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin', 'repository.write', 'repository.read',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    repo_id = repo.repo_id
    cache_seconds = safe_int(rhodecode.CONFIG.get('rc_cache.cache_repo.expiration_time'))
    cache_on = cache_seconds > 0

    cache_namespace_uid = 'cache_repo.{}'.format(repo_id)
    region = rc_cache.get_or_create_region('cache_repo', cache_namespace_uid)

    def compute_fts_tree(cache_ver, repo_id, commit_id, root_path):
        return ScmModel().get_fts_data(repo_id, commit_id, root_path)

    try:
        # check if repo is not empty by any chance, skip quicker if it is.
        _scm = repo.scm_instance()
        if _scm.is_empty():
            return []
    except RepositoryError:
        log.exception("Exception occurred while trying to get repo nodes")
        raise JSONRPCError('failed to get repo: `%s` nodes' % repo.repo_name)

    try:
        # we need to resolve commit_id to a FULL sha for cache to work correctly.
        # sending 'master' is a pointer that needs to be translated to current commit.
        commit_id = _scm.get_commit(commit_id=commit_id).raw_id
        log.debug(
            'Computing FTS REPO TREE for repo_id %s commit_id `%s` '
            'with caching: %s[TTL: %ss]' % (
                repo_id, commit_id, cache_on, cache_seconds or 0))

        tree_files = compute_fts_tree(rc_cache.FILE_TREE_CACHE_VER, repo_id, commit_id, root_path)
        return tree_files

    except Exception:
        log.exception("Exception occurred while trying to get repo nodes")
        raise JSONRPCError('failed to get repo: `%s` nodes' % repo.repo_name)


@jsonrpc_method()
def get_repo_refs(request, apiuser, repoid):
    """
    Returns a dictionary of current references. It returns
    bookmarks, branches, closed_branches, and tags for given repository

    It's possible to specify ret_type to show only `files` or `dirs`.

    This command can only be run using an |authtoken| with admin rights,
    or users with at least read rights to |repos|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: The repository name or repository ID.
    :type repoid: str or int

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        "result": {
            "bookmarks": {
              "dev": "5611d30200f4040ba2ab4f3d64e5b06408a02188",
              "master": "367f590445081d8ec8c2ea0456e73ae1f1c3d6cf"
            },
            "branches": {
              "default": "5611d30200f4040ba2ab4f3d64e5b06408a02188",
              "stable": "367f590445081d8ec8c2ea0456e73ae1f1c3d6cf"
            },
            "branches_closed": {},
            "tags": {
              "tip": "5611d30200f4040ba2ab4f3d64e5b06408a02188",
              "v4.4.0": "1232313f9e6adac5ce5399c2a891dc1e72b79022",
              "v4.4.1": "cbb9f1d329ae5768379cdec55a62ebdd546c4e27",
              "v4.4.2": "24ffe44a27fcd1c5b6936144e176b9f6dd2f3a17",
            }
        }
        error:  null
    """

    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin', 'repository.write', 'repository.read',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    try:
        # check if repo is not empty by any chance, skip quicker if it is.
        vcs_instance = repo.scm_instance()
        refs = vcs_instance.refs()
        return refs
    except Exception:
        log.exception("Exception occurred while trying to get repo refs")
        raise JSONRPCError(
            'failed to get repo: `%s` references' % repo.repo_name
        )


@jsonrpc_method()
def create_repo(
        request, apiuser, repo_name, repo_type,
        owner=Optional(OAttr('apiuser')),
        description=Optional(''),
        private=Optional(False),
        clone_uri=Optional(None),
        push_uri=Optional(None),
        landing_rev=Optional(None),
        enable_statistics=Optional(False),
        enable_locking=Optional(False),
        enable_downloads=Optional(False),
        copy_permissions=Optional(False)):
    """
    Creates a repository.

    * If the repository name contains "/", repository will be created inside
      a repository group or nested repository groups

      For example "foo/bar/repo1" will create |repo| called "repo1" inside
      group "foo/bar". You have to have permissions to access and write to
      the last repository group ("bar" in this example)

    This command can only be run using an |authtoken| with at least
    permissions to create repositories, or write permissions to
    parent repository groups.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repo_name: Set the repository name.
    :type repo_name: str
    :param repo_type: Set the repository type; 'hg','git', or 'svn'.
    :type repo_type: str
    :param owner: user_id or username
    :type owner: Optional(str)
    :param description: Set the repository description.
    :type description: Optional(str)
    :param private: set repository as private
    :type private: bool
    :param clone_uri: set clone_uri
    :type clone_uri: str
    :param push_uri: set push_uri
    :type push_uri: str
    :param landing_rev: <rev_type>:<rev>, e.g branch:default, book:dev, rev:abcd
    :type landing_rev: str
    :param enable_locking:
    :type enable_locking: bool
    :param enable_downloads:
    :type enable_downloads: bool
    :param enable_statistics:
    :type enable_statistics: bool
    :param copy_permissions: Copy permission from group in which the
        repository is being created.
    :type copy_permissions: bool


    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result: {
                  "msg": "Created new repository `<reponame>`",
                  "success": true,
                  "task": "<celery task id or None if done sync>"
                }
        error:  null


    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
         'failed to create repository `<repo_name>`'
      }

    """

    owner = validate_set_owner_permissions(apiuser, owner)

    description = Optional.extract(description)
    copy_permissions = Optional.extract(copy_permissions)
    clone_uri = Optional.extract(clone_uri)
    push_uri = Optional.extract(push_uri)

    defs = SettingsModel().get_default_repo_settings(strip_prefix=True)
    if isinstance(private, Optional):
        private = defs.get('repo_private') or Optional.extract(private)
    if isinstance(repo_type, Optional):
        repo_type = defs.get('repo_type')
    if isinstance(enable_statistics, Optional):
        enable_statistics = defs.get('repo_enable_statistics')
    if isinstance(enable_locking, Optional):
        enable_locking = defs.get('repo_enable_locking')
    if isinstance(enable_downloads, Optional):
        enable_downloads = defs.get('repo_enable_downloads')

    landing_ref, _label = ScmModel.backend_landing_ref(repo_type)
    ref_choices, _labels = ScmModel().get_repo_landing_revs(request.translate)
    ref_choices = list(set(ref_choices + [landing_ref]))

    landing_commit_ref = Optional.extract(landing_rev) or landing_ref

    schema = repo_schema.RepoSchema().bind(
        repo_type_options=rhodecode.BACKENDS.keys(),
        repo_ref_options=ref_choices,
        repo_type=repo_type,
        # user caller
        user=apiuser)

    try:
        schema_data = schema.deserialize(dict(
            repo_name=repo_name,
            repo_type=repo_type,
            repo_owner=owner.username,
            repo_description=description,
            repo_landing_commit_ref=landing_commit_ref,
            repo_clone_uri=clone_uri,
            repo_push_uri=push_uri,
            repo_private=private,
            repo_copy_permissions=copy_permissions,
            repo_enable_statistics=enable_statistics,
            repo_enable_downloads=enable_downloads,
            repo_enable_locking=enable_locking))
    except validation_schema.Invalid as err:
        raise JSONRPCValidationError(colander_exc=err)

    try:
        data = {
            'owner': owner,
            'repo_name': schema_data['repo_group']['repo_name_without_group'],
            'repo_name_full': schema_data['repo_name'],
            'repo_group': schema_data['repo_group']['repo_group_id'],
            'repo_type': schema_data['repo_type'],
            'repo_description': schema_data['repo_description'],
            'repo_private': schema_data['repo_private'],
            'clone_uri': schema_data['repo_clone_uri'],
            'push_uri': schema_data['repo_push_uri'],
            'repo_landing_rev': schema_data['repo_landing_commit_ref'],
            'enable_statistics': schema_data['repo_enable_statistics'],
            'enable_locking': schema_data['repo_enable_locking'],
            'enable_downloads': schema_data['repo_enable_downloads'],
            'repo_copy_permissions': schema_data['repo_copy_permissions'],
        }

        task = RepoModel().create(form_data=data, cur_user=owner.user_id)
        task_id = get_task_id(task)
        # no commit, it's done in RepoModel, or async via celery
        return {
            'msg': "Created new repository `%s`" % (schema_data['repo_name'],),
            'success': True,  # cannot return the repo data here since fork
            # can be done async
            'task': task_id
        }
    except Exception:
        log.exception(
            u"Exception while trying to create the repository %s",
            schema_data['repo_name'])
        raise JSONRPCError(
            'failed to create repository `%s`' % (schema_data['repo_name'],))


@jsonrpc_method()
def add_field_to_repo(request, apiuser, repoid, key, label=Optional(''),
                      description=Optional('')):
    """
    Adds an extra field to a repository.

    This command can only be run using an |authtoken| with at least
    write permissions to the |repo|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Set the repository name or repository id.
    :type repoid: str or int
    :param key: Create a unique field key for this repository.
    :type key: str
    :param label:
    :type label: Optional(str)
    :param description:
    :type description: Optional(str)
    """
    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    label = Optional.extract(label) or key
    description = Optional.extract(description)

    field = RepositoryField.get_by_key_name(key, repo)
    if field:
        raise JSONRPCError('Field with key '
                           '`%s` exists for repo `%s`' % (key, repoid))

    try:
        RepoModel().add_repo_field(repo, key, field_label=label,
                                   field_desc=description)
        Session().commit()
        return {
            'msg': "Added new repository field `%s`" % (key,),
            'success': True,
        }
    except Exception:
        log.exception("Exception occurred while trying to add field to repo")
        raise JSONRPCError(
            'failed to create new field for repository `%s`' % (repoid,))


@jsonrpc_method()
def remove_field_from_repo(request, apiuser, repoid, key):
    """
    Removes an extra field from a repository.

    This command can only be run using an |authtoken| with at least
    write permissions to the |repo|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Set the repository name or repository ID.
    :type repoid: str or int
    :param key: Set the unique field key for this repository.
    :type key: str
    """

    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    field = RepositoryField.get_by_key_name(key, repo)
    if not field:
        raise JSONRPCError('Field with key `%s` does not '
                           'exists for repo `%s`' % (key, repoid))

    try:
        RepoModel().delete_repo_field(repo, field_key=key)
        Session().commit()
        return {
            'msg': "Deleted repository field `%s`" % (key,),
            'success': True,
        }
    except Exception:
        log.exception(
            "Exception occurred while trying to delete field from repo")
        raise JSONRPCError(
            'failed to delete field for repository `%s`' % (repoid,))


@jsonrpc_method()
def update_repo(
        request, apiuser, repoid, repo_name=Optional(None),
        owner=Optional(OAttr('apiuser')), description=Optional(''),
        private=Optional(False),
        clone_uri=Optional(None), push_uri=Optional(None),
        landing_rev=Optional(None), fork_of=Optional(None),
        enable_statistics=Optional(False),
        enable_locking=Optional(False),
        enable_downloads=Optional(False), fields=Optional('')):
    """
    Updates a repository with the given information.

    This command can only be run using an |authtoken| with at least
    admin permissions to the |repo|.

    * If the repository name contains "/", repository will be updated
      accordingly with a repository group or nested repository groups

      For example repoid=repo-test name="foo/bar/repo-test" will update |repo|
      called "repo-test" and place it inside group "foo/bar".
      You have to have permissions to access and write to the last repository
      group ("bar" in this example)

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: repository name or repository ID.
    :type repoid: str or int
    :param repo_name: Update the |repo| name, including the
        repository group it's in.
    :type repo_name: str
    :param owner: Set the |repo| owner.
    :type owner: str
    :param fork_of: Set the |repo| as fork of another |repo|.
    :type fork_of: str
    :param description: Update the |repo| description.
    :type description: str
    :param private: Set the |repo| as private. (True | False)
    :type private: bool
    :param clone_uri: Update the |repo| clone URI.
    :type clone_uri: str
    :param landing_rev: Set the |repo| landing revision. e.g branch:default, book:dev, rev:abcd
    :type landing_rev: str
    :param enable_statistics: Enable statistics on the |repo|, (True | False).
    :type enable_statistics: bool
    :param enable_locking: Enable |repo| locking.
    :type enable_locking: bool
    :param enable_downloads: Enable downloads from the |repo|, (True | False).
    :type enable_downloads: bool
    :param fields: Add extra fields to the |repo|. Use the following
        example format: ``field_key=field_val,field_key2=fieldval2``.
        Escape ', ' with \,
    :type fields: str
    """

    repo = get_repo_or_error(repoid)

    include_secrets = False
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)
    else:
        include_secrets = True

    updates = dict(
        repo_name=repo_name
        if not isinstance(repo_name, Optional) else repo.repo_name,

        fork_id=fork_of
        if not isinstance(fork_of, Optional) else repo.fork.repo_name if repo.fork else None,

        user=owner
        if not isinstance(owner, Optional) else repo.user.username,

        repo_description=description
        if not isinstance(description, Optional) else repo.description,

        repo_private=private
        if not isinstance(private, Optional) else repo.private,

        clone_uri=clone_uri
        if not isinstance(clone_uri, Optional) else repo.clone_uri,

        push_uri=push_uri
        if not isinstance(push_uri, Optional) else repo.push_uri,

        repo_landing_rev=landing_rev
        if not isinstance(landing_rev, Optional) else repo._landing_revision,

        repo_enable_statistics=enable_statistics
        if not isinstance(enable_statistics, Optional) else repo.enable_statistics,

        repo_enable_locking=enable_locking
        if not isinstance(enable_locking, Optional) else repo.enable_locking,

        repo_enable_downloads=enable_downloads
        if not isinstance(enable_downloads, Optional) else repo.enable_downloads)

    landing_ref, _label = ScmModel.backend_landing_ref(repo.repo_type)
    ref_choices, _labels = ScmModel().get_repo_landing_revs(
        request.translate, repo=repo)
    ref_choices = list(set(ref_choices + [landing_ref]))

    old_values = repo.get_api_data()
    repo_type = repo.repo_type
    schema = repo_schema.RepoSchema().bind(
        repo_type_options=rhodecode.BACKENDS.keys(),
        repo_ref_options=ref_choices,
        repo_type=repo_type,
        # user caller
        user=apiuser,
        old_values=old_values)
    try:
        schema_data = schema.deserialize(dict(
            # we save old value, users cannot change type
            repo_type=repo_type,

            repo_name=updates['repo_name'],
            repo_owner=updates['user'],
            repo_description=updates['repo_description'],
            repo_clone_uri=updates['clone_uri'],
            repo_push_uri=updates['push_uri'],
            repo_fork_of=updates['fork_id'],
            repo_private=updates['repo_private'],
            repo_landing_commit_ref=updates['repo_landing_rev'],
            repo_enable_statistics=updates['repo_enable_statistics'],
            repo_enable_downloads=updates['repo_enable_downloads'],
            repo_enable_locking=updates['repo_enable_locking']))
    except validation_schema.Invalid as err:
        raise JSONRPCValidationError(colander_exc=err)

    # save validated data back into the updates dict
    validated_updates = dict(
        repo_name=schema_data['repo_group']['repo_name_without_group'],
        repo_group=schema_data['repo_group']['repo_group_id'],

        user=schema_data['repo_owner'],
        repo_description=schema_data['repo_description'],
        repo_private=schema_data['repo_private'],
        clone_uri=schema_data['repo_clone_uri'],
        push_uri=schema_data['repo_push_uri'],
        repo_landing_rev=schema_data['repo_landing_commit_ref'],
        repo_enable_statistics=schema_data['repo_enable_statistics'],
        repo_enable_locking=schema_data['repo_enable_locking'],
        repo_enable_downloads=schema_data['repo_enable_downloads'],
    )

    if schema_data['repo_fork_of']:
        fork_repo = get_repo_or_error(schema_data['repo_fork_of'])
        validated_updates['fork_id'] = fork_repo.repo_id

    # extra fields
    fields = parse_args(Optional.extract(fields), key_prefix='ex_')
    if fields:
        validated_updates.update(fields)

    try:
        RepoModel().update(repo, **validated_updates)
        audit_logger.store_api(
            'repo.edit', action_data={'old_data': old_values},
            user=apiuser, repo=repo)
        Session().commit()
        return {
            'msg': 'updated repo ID:%s %s' % (repo.repo_id, repo.repo_name),
            'repository': repo.get_api_data(include_secrets=include_secrets)
        }
    except Exception:
        log.exception(
            u"Exception while trying to update the repository %s",
            repoid)
        raise JSONRPCError('failed to update repo `%s`' % repoid)


@jsonrpc_method()
def fork_repo(request, apiuser, repoid, fork_name,
              owner=Optional(OAttr('apiuser')),
              description=Optional(''),
              private=Optional(False),
              clone_uri=Optional(None),
              landing_rev=Optional(None),
              copy_permissions=Optional(False)):
    """
    Creates a fork of the specified |repo|.

    * If the fork_name contains "/", fork will be created inside
      a repository group or nested repository groups

      For example "foo/bar/fork-repo" will create fork called "fork-repo"
      inside group "foo/bar". You have to have permissions to access and
      write to the last repository group ("bar" in this example)

    This command can only be run using an |authtoken| with minimum
    read permissions of the forked repo, create fork permissions for an user.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Set repository name or repository ID.
    :type repoid: str or int
    :param fork_name: Set the fork name, including it's repository group membership.
    :type fork_name: str
    :param owner: Set the fork owner.
    :type owner: str
    :param description: Set the fork description.
    :type description: str
    :param copy_permissions: Copy permissions from parent |repo|. The
        default is False.
    :type copy_permissions: bool
    :param private: Make the fork private. The default is False.
    :type private: bool
    :param landing_rev: Set the landing revision. E.g branch:default, book:dev, rev:abcd

    Example output:

    .. code-block:: bash

        id : <id_for_response>
        api_key : "<api_key>"
        args:     {
                    "repoid" :          "<reponame or repo_id>",
                    "fork_name":        "<forkname>",
                    "owner":            "<username or user_id = Optional(=apiuser)>",
                    "description":      "<description>",
                    "copy_permissions": "<bool>",
                    "private":          "<bool>",
                    "landing_rev":      "<landing_rev>"
                  }

    Example error output:

    .. code-block:: bash

        id : <id_given_in_input>
        result: {
                  "msg": "Created fork of `<reponame>` as `<forkname>`",
                  "success": true,
                  "task": "<celery task id or None if done sync>"
                }
        error:  null

    """

    repo = get_repo_or_error(repoid)
    repo_name = repo.repo_name

    if not has_superadmin_permission(apiuser):
        # check if we have at least read permission for
        # this repo that we fork !
        _perms = ('repository.admin', 'repository.write', 'repository.read')
        validate_repo_permissions(apiuser, repoid, repo, _perms)

        # check if the regular user has at least fork permissions as well
        if not HasPermissionAnyApi(PermissionModel.FORKING_ENABLED)(user=apiuser):
            raise JSONRPCForbidden()

    # check if user can set owner parameter
    owner = validate_set_owner_permissions(apiuser, owner)

    description = Optional.extract(description)
    copy_permissions = Optional.extract(copy_permissions)
    clone_uri = Optional.extract(clone_uri)

    landing_ref, _label = ScmModel.backend_landing_ref(repo.repo_type)
    ref_choices, _labels = ScmModel().get_repo_landing_revs(request.translate)
    ref_choices = list(set(ref_choices + [landing_ref]))
    landing_commit_ref = Optional.extract(landing_rev) or landing_ref

    private = Optional.extract(private)

    schema = repo_schema.RepoSchema().bind(
        repo_type_options=rhodecode.BACKENDS.keys(),
        repo_ref_options=ref_choices,
        repo_type=repo.repo_type,
        # user caller
        user=apiuser)

    try:
        schema_data = schema.deserialize(dict(
            repo_name=fork_name,
            repo_type=repo.repo_type,
            repo_owner=owner.username,
            repo_description=description,
            repo_landing_commit_ref=landing_commit_ref,
            repo_clone_uri=clone_uri,
            repo_private=private,
            repo_copy_permissions=copy_permissions))
    except validation_schema.Invalid as err:
        raise JSONRPCValidationError(colander_exc=err)

    try:
        data = {
            'fork_parent_id': repo.repo_id,

            'repo_name': schema_data['repo_group']['repo_name_without_group'],
            'repo_name_full': schema_data['repo_name'],
            'repo_group': schema_data['repo_group']['repo_group_id'],
            'repo_type': schema_data['repo_type'],
            'description': schema_data['repo_description'],
            'private': schema_data['repo_private'],
            'copy_permissions': schema_data['repo_copy_permissions'],
            'landing_rev': schema_data['repo_landing_commit_ref'],
        }

        task = RepoModel().create_fork(data, cur_user=owner.user_id)
        # no commit, it's done in RepoModel, or async via celery
        task_id = get_task_id(task)

        return {
            'msg': 'Created fork of `%s` as `%s`' % (
                repo.repo_name, schema_data['repo_name']),
            'success': True,  # cannot return the repo data here since fork
            # can be done async
            'task': task_id
        }
    except Exception:
        log.exception(
            u"Exception while trying to create fork %s",
            schema_data['repo_name'])
        raise JSONRPCError(
            'failed to fork repository `%s` as `%s`' % (
                repo_name, schema_data['repo_name']))


@jsonrpc_method()
def delete_repo(request, apiuser, repoid, forks=Optional('')):
    """
    Deletes a repository.

    * When the `forks` parameter is set it's possible to detach or delete
      forks of deleted repository.

    This command can only be run using an |authtoken| with admin
    permissions on the |repo|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Set the repository name or repository ID.
    :type repoid: str or int
    :param forks: Set to `detach` or `delete` forks from the |repo|.
    :type forks: Optional(str)

    Example error output:

    .. code-block:: bash

        id : <id_given_in_input>
        result: {
                  "msg": "Deleted repository `<reponame>`",
                  "success": true
                }
        error:  null
    """

    repo = get_repo_or_error(repoid)
    repo_name = repo.repo_name
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    try:
        handle_forks = Optional.extract(forks)
        _forks_msg = ''
        _forks = [f for f in repo.forks]
        if handle_forks == 'detach':
            _forks_msg = ' ' + 'Detached %s forks' % len(_forks)
        elif handle_forks == 'delete':
            _forks_msg = ' ' + 'Deleted %s forks' % len(_forks)
        elif _forks:
            raise JSONRPCError(
                'Cannot delete `%s` it still contains attached forks' %
                (repo.repo_name,)
            )
        old_data = repo.get_api_data()
        RepoModel().delete(repo, forks=forks)

        repo = audit_logger.RepoWrap(repo_id=None,
                                     repo_name=repo.repo_name)

        audit_logger.store_api(
            'repo.delete', action_data={'old_data': old_data},
            user=apiuser, repo=repo)

        ScmModel().mark_for_invalidation(repo_name, delete=True)
        Session().commit()
        return {
            'msg': 'Deleted repository `%s`%s' % (repo_name, _forks_msg),
            'success': True
        }
    except Exception:
        log.exception("Exception occurred while trying to delete repo")
        raise JSONRPCError(
            'failed to delete repository `%s`' % (repo_name,)
        )


#TODO: marcink, change name ?
@jsonrpc_method()
def invalidate_cache(request, apiuser, repoid, delete_keys=Optional(False)):
    """
    Invalidates the cache for the specified repository.

    This command can only be run using an |authtoken| with admin rights to
    the specified repository.

    This command takes the following options:

    :param apiuser: This is filled automatically from |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Sets the repository name or repository ID.
    :type repoid: str or int
    :param delete_keys: This deletes the invalidated keys instead of
        just flagging them.
    :type delete_keys: Optional(``True`` | ``False``)

    Example output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : {
        'msg': Cache for repository `<repository name>` was invalidated,
        'repository': <repository name>
      }
      error :  null

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error : {
         'Error occurred during cache invalidation action'
      }

    """

    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin', 'repository.write',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    delete = Optional.extract(delete_keys)
    try:
        ScmModel().mark_for_invalidation(repo.repo_name, delete=delete)
        return {
            'msg': 'Cache for repository `%s` was invalidated' % (repoid,),
            'repository': repo.repo_name
        }
    except Exception:
        log.exception(
            "Exception occurred while trying to invalidate repo cache")
        raise JSONRPCError(
            'Error occurred during cache invalidation action'
        )


#TODO: marcink, change name ?
@jsonrpc_method()
def lock(request, apiuser, repoid, locked=Optional(None),
         userid=Optional(OAttr('apiuser'))):
    """
    Sets the lock state of the specified |repo| by the given user.
    From more information, see :ref:`repo-locking`.

    * If the ``userid`` option is not set, the repository is locked to the
      user who called the method.
    * If the ``locked`` parameter is not set, the current lock state of the
      repository is displayed.

    This command can only be run using an |authtoken| with admin rights to
    the specified repository.

    This command takes the following options:

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Sets the repository name or repository ID.
    :type repoid: str or int
    :param locked: Sets the lock state.
    :type locked: Optional(``True`` | ``False``)
    :param userid: Set the repository lock to this user.
    :type userid: Optional(str or int)

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : {
        'repo': '<reponame>',
        'locked': <bool: lock state>,
        'locked_since': <int: lock timestamp>,
        'locked_by': <username of person who made the lock>,
        'lock_reason': <str: reason for locking>,
        'lock_state_changed': <bool: True if lock state has been changed in this request>,
        'msg': 'Repo `<reponame>` locked by `<username>` on <timestamp>.'
        or
        'msg': 'Repo `<repository name>` not locked.'
        or
        'msg': 'User `<user name>` set lock state for repo `<repository name>` to `<new lock state>`'
      }
      error :  null

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
        'Error occurred locking repository `<reponame>`'
      }
    """

    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        # check if we have at least write permission for this repo !
        _perms = ('repository.admin', 'repository.write',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

        # make sure normal user does not pass someone else userid,
        # he is not allowed to do that
        if not isinstance(userid, Optional) and userid != apiuser.user_id:
            raise JSONRPCError('userid is not the same as your user')

    if isinstance(userid, Optional):
        userid = apiuser.user_id

    user = get_user_or_error(userid)

    if isinstance(locked, Optional):
        lockobj = repo.locked

        if lockobj[0] is None:
            _d = {
                'repo': repo.repo_name,
                'locked': False,
                'locked_since': None,
                'locked_by': None,
                'lock_reason': None,
                'lock_state_changed': False,
                'msg': 'Repo `%s` not locked.' % repo.repo_name
            }
            return _d
        else:
            _user_id, _time, _reason = lockobj
            lock_user = get_user_or_error(userid)
            _d = {
                'repo': repo.repo_name,
                'locked': True,
                'locked_since': _time,
                'locked_by': lock_user.username,
                'lock_reason': _reason,
                'lock_state_changed': False,
                'msg': ('Repo `%s` locked by `%s` on `%s`.'
                        % (repo.repo_name, lock_user.username,
                           json.dumps(time_to_datetime(_time))))
            }
            return _d

    # force locked state through a flag
    else:
        locked = str2bool(locked)
        lock_reason = Repository.LOCK_API
        try:
            if locked:
                lock_time = time.time()
                Repository.lock(repo, user.user_id, lock_time, lock_reason)
            else:
                lock_time = None
                Repository.unlock(repo)
            _d = {
                'repo': repo.repo_name,
                'locked': locked,
                'locked_since': lock_time,
                'locked_by': user.username,
                'lock_reason': lock_reason,
                'lock_state_changed': True,
                'msg': ('User `%s` set lock state for repo `%s` to `%s`'
                        % (user.username, repo.repo_name, locked))
            }
            return _d
        except Exception:
            log.exception(
                "Exception occurred while trying to lock repository")
            raise JSONRPCError(
                'Error occurred locking repository `%s`' % repo.repo_name
            )


@jsonrpc_method()
def comment_commit(
        request, apiuser, repoid, commit_id, message, status=Optional(None),
        comment_type=Optional(ChangesetComment.COMMENT_TYPE_NOTE),
        resolves_comment_id=Optional(None), extra_recipients=Optional([]),
        userid=Optional(OAttr('apiuser')), send_email=Optional(True)):
    """
    Set a commit comment, and optionally change the status of the commit.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Set the repository name or repository ID.
    :type repoid: str or int
    :param commit_id: Specify the commit_id for which to set a comment.
    :type commit_id: str
    :param message: The comment text.
    :type message: str
    :param status: (**Optional**) status of commit, one of: 'not_reviewed',
        'approved', 'rejected', 'under_review'
    :type status: str
    :param comment_type: Comment type, one of: 'note', 'todo'
    :type comment_type: Optional(str), default: 'note'
    :param resolves_comment_id: id of comment which this one will resolve
    :type resolves_comment_id: Optional(int)
    :param extra_recipients: list of user ids or usernames to add
        notifications for this comment. Acts like a CC for notification
    :type extra_recipients: Optional(list)
    :param userid: Set the user name of the comment creator.
    :type userid: Optional(str or int)
    :param send_email: Define if this comment should also send email notification
    :type send_email: Optional(bool)

    Example error output:

    .. code-block:: bash

        {
            "id" : <id_given_in_input>,
            "result" : {
                "msg": "Commented on commit `<commit_id>` for repository `<repoid>`",
                "status_change": null or <status>,
                "success": true
            },
            "error" :  null
        }

    """
    _ = request.translate

    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.read', 'repository.write', 'repository.admin')
        validate_repo_permissions(apiuser, repoid, repo, _perms)
    db_repo_name = repo.repo_name

    try:
        commit = repo.scm_instance().get_commit(commit_id=commit_id)
        commit_id = commit.raw_id
    except Exception as e:
        log.exception('Failed to fetch commit')
        raise JSONRPCError(safe_str(e))

    if isinstance(userid, Optional):
        userid = apiuser.user_id

    user = get_user_or_error(userid)
    status = Optional.extract(status)
    comment_type = Optional.extract(comment_type)
    resolves_comment_id = Optional.extract(resolves_comment_id)
    extra_recipients = Optional.extract(extra_recipients)
    send_email = Optional.extract(send_email, binary=True)

    allowed_statuses = [x[0] for x in ChangesetStatus.STATUSES]
    if status and status not in allowed_statuses:
        raise JSONRPCError('Bad status, must be on '
                           'of %s got %s' % (allowed_statuses, status,))

    if resolves_comment_id:
        comment = ChangesetComment.get(resolves_comment_id)
        if not comment:
            raise JSONRPCError(
                'Invalid resolves_comment_id `%s` for this commit.'
                % resolves_comment_id)
        if comment.comment_type != ChangesetComment.COMMENT_TYPE_TODO:
            raise JSONRPCError(
                'Comment `%s` is wrong type for setting status to resolved.'
                % resolves_comment_id)

    try:
        rc_config = SettingsModel().get_all_settings()
        renderer = rc_config.get('rhodecode_markup_renderer', 'rst')
        status_change_label = ChangesetStatus.get_status_lbl(status)
        comment = CommentsModel().create(
            message, repo, user, commit_id=commit_id,
            status_change=status_change_label,
            status_change_type=status,
            renderer=renderer,
            comment_type=comment_type,
            resolves_comment_id=resolves_comment_id,
            auth_user=apiuser,
            extra_recipients=extra_recipients,
            send_email=send_email
        )
        is_inline = comment.is_inline

        if status:
            # also do a status change
            try:
                ChangesetStatusModel().set_status(
                    repo, status, user, comment, revision=commit_id,
                    dont_allow_on_closed_pull_request=True
                )
            except StatusChangeOnClosedPullRequestError:
                log.exception(
                    "Exception occurred while trying to change repo commit status")
                msg = ('Changing status on a commit associated with '
                       'a closed pull request is not allowed')
                raise JSONRPCError(msg)

        CommentsModel().trigger_commit_comment_hook(
            repo, apiuser, 'create',
            data={'comment': comment, 'commit': commit})

        Session().commit()

        comment_broadcast_channel = channelstream.comment_channel(
            db_repo_name, commit_obj=commit)

        comment_data = {'comment': comment, 'comment_id': comment.comment_id}
        comment_type = 'inline' if is_inline else 'general'
        channelstream.comment_channelstream_push(
            request, comment_broadcast_channel, apiuser,
            _('posted a new {} comment').format(comment_type),
            comment_data=comment_data)

        return {
            'msg': (
                'Commented on commit `%s` for repository `%s`' % (
                    comment.revision, repo.repo_name)),
            'status_change': status,
            'success': True,
        }
    except JSONRPCError:
        # catch any inside errors, and re-raise them to prevent from
        # below global catch to silence them
        raise
    except Exception:
        log.exception("Exception occurred while trying to comment on commit")
        raise JSONRPCError(
            'failed to set comment on repository `%s`' % (repo.repo_name,)
        )


@jsonrpc_method()
def get_repo_comments(request, apiuser, repoid,
                      commit_id=Optional(None), comment_type=Optional(None),
                      userid=Optional(None)):
    """
    Get all comments for a repository

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Set the repository name or repository ID.
    :type repoid: str or int
    :param commit_id: Optionally filter the comments by the commit_id
    :type commit_id: Optional(str), default: None
    :param comment_type: Optionally filter the comments by the comment_type
        one of: 'note', 'todo'
    :type comment_type: Optional(str), default: None
    :param userid: Optionally filter the comments by the author of comment
    :type userid: Optional(str or int), Default: None

    Example error output:

    .. code-block:: bash

        {
            "id" : <id_given_in_input>,
            "result" : [
                {
                  "comment_author": <USER_DETAILS>,
                  "comment_created_on": "2017-02-01T14:38:16.309",
                  "comment_f_path": "file.txt",
                  "comment_id": 282,
                  "comment_lineno": "n1",
                  "comment_resolved_by": null,
                  "comment_status": [],
                  "comment_text": "This file needs a header",
                  "comment_type": "todo",
                  "comment_last_version: 0
                }
            ],
            "error" :  null
        }

    """
    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.read', 'repository.write', 'repository.admin')
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    commit_id = Optional.extract(commit_id)

    userid = Optional.extract(userid)
    if userid:
        user = get_user_or_error(userid)
    else:
        user = None

    comment_type = Optional.extract(comment_type)
    if comment_type and comment_type not in ChangesetComment.COMMENT_TYPES:
        raise JSONRPCError(
                'comment_type must be one of `{}` got {}'.format(
                    ChangesetComment.COMMENT_TYPES, comment_type)
            )

    comments = CommentsModel().get_repository_comments(
        repo=repo, comment_type=comment_type, user=user, commit_id=commit_id)
    return comments


@jsonrpc_method()
def get_comment(request, apiuser, comment_id):
    """
    Get single comment from repository or pull_request

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param comment_id: comment id found in the URL of comment
    :type comment_id: str or int

    Example error output:

    .. code-block:: bash

        {
            "id" : <id_given_in_input>,
            "result" : {
                  "comment_author": <USER_DETAILS>,
                  "comment_created_on": "2017-02-01T14:38:16.309",
                  "comment_f_path": "file.txt",
                  "comment_id": 282,
                  "comment_lineno": "n1",
                  "comment_resolved_by": null,
                  "comment_status": [],
                  "comment_text": "This file needs a header",
                  "comment_type": "todo",
                  "comment_last_version: 0
            },
            "error" :  null
        }

    """

    comment = ChangesetComment.get(comment_id)
    if not comment:
        raise JSONRPCError('comment `%s` does not exist' % (comment_id,))

    perms = ('repository.read', 'repository.write', 'repository.admin')
    has_comment_perm = HasRepoPermissionAnyApi(*perms)\
        (user=apiuser, repo_name=comment.repo.repo_name)

    if not has_comment_perm:
        raise JSONRPCError('comment `%s` does not exist' % (comment_id,))

    return comment


@jsonrpc_method()
def edit_comment(request, apiuser, message, comment_id, version,
                 userid=Optional(OAttr('apiuser'))):
    """
    Edit comment on the pull request or commit,
    specified by the `comment_id` and version. Initially version should be 0

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param comment_id: Specify the comment_id for editing
    :type comment_id: int
    :param version: version of the comment that will be created, starts from 0
    :type version: int
    :param message: The text content of the comment.
    :type message: str
    :param userid: Comment on the pull request as this user
    :type userid: Optional(str or int)

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result : {
            "comment": "<comment data>",
            "version": "<Integer>",
        },
        error :  null
    """

    auth_user = apiuser
    comment = ChangesetComment.get(comment_id)
    if not comment:
        raise JSONRPCError('comment `%s` does not exist' % (comment_id,))

    is_super_admin = has_superadmin_permission(apiuser)
    is_repo_admin = HasRepoPermissionAnyApi('repository.admin')\
        (user=apiuser, repo_name=comment.repo.repo_name)

    if not isinstance(userid, Optional):
        if is_super_admin or is_repo_admin:
            apiuser = get_user_or_error(userid)
            auth_user = apiuser.AuthUser()
        else:
            raise JSONRPCError('userid is not the same as your user')

    comment_author = comment.author.user_id == auth_user.user_id
    if not (comment.immutable is False and (is_super_admin or is_repo_admin) or comment_author):
        raise JSONRPCError("you don't have access to edit this comment")

    try:
        comment_history = CommentsModel().edit(
            comment_id=comment_id,
            text=message,
            auth_user=auth_user,
            version=version,
        )
        Session().commit()
    except CommentVersionMismatch:
        raise JSONRPCError(
            'comment ({}) version ({}) mismatch'.format(comment_id, version)
        )
    if not comment_history and not message:
        raise JSONRPCError(
            "comment ({}) can't be changed with empty string".format(comment_id)
        )

    if comment.pull_request:
        pull_request = comment.pull_request
        PullRequestModel().trigger_pull_request_hook(
            pull_request, apiuser, 'comment_edit',
            data={'comment': comment})
    else:
        db_repo = comment.repo
        commit_id = comment.revision
        commit = db_repo.get_commit(commit_id)
        CommentsModel().trigger_commit_comment_hook(
            db_repo, apiuser, 'edit',
            data={'comment': comment, 'commit': commit})

    data = {
        'comment': comment,
        'version': comment_history.version if comment_history else None,
    }
    return data


# TODO(marcink): write this with all required logic for deleting a comments in PR or commits
# @jsonrpc_method()
# def delete_comment(request, apiuser, comment_id):
#     auth_user = apiuser
#
#     comment = ChangesetComment.get(comment_id)
#     if not comment:
#         raise JSONRPCError('comment `%s` does not exist' % (comment_id,))
#
#     is_super_admin = has_superadmin_permission(apiuser)
#     is_repo_admin = HasRepoPermissionAnyApi('repository.admin')\
#         (user=apiuser, repo_name=comment.repo.repo_name)
#
#     comment_author = comment.author.user_id == auth_user.user_id
#     if not (comment.immutable is False and (is_super_admin or is_repo_admin) or comment_author):
#         raise JSONRPCError("you don't have access to edit this comment")

@jsonrpc_method()
def grant_user_permission(request, apiuser, repoid, userid, perm):
    """
    Grant permissions for the specified user on the given repository,
    or update existing permissions if found.

    This command can only be run using an |authtoken| with admin
    permissions on the |repo|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Set the repository name or repository ID.
    :type repoid: str or int
    :param userid: Set the user name.
    :type userid: str
    :param perm: Set the user permissions, using the following format
        ``(repository.(none|read|write|admin))``
    :type perm: str

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result: {
                  "msg" : "Granted perm: `<perm>` for user: `<username>` in repo: `<reponame>`",
                  "success": true
                }
        error:  null
    """

    repo = get_repo_or_error(repoid)
    user = get_user_or_error(userid)
    perm = get_perm_or_error(perm)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    perm_additions = [[user.user_id, perm.permission_name, "user"]]
    try:
        changes = RepoModel().update_permissions(
            repo=repo, perm_additions=perm_additions, cur_user=apiuser)

        action_data = {
            'added': changes['added'],
            'updated': changes['updated'],
            'deleted': changes['deleted'],
        }
        audit_logger.store_api(
            'repo.edit.permissions', action_data=action_data, user=apiuser, repo=repo)
        Session().commit()
        PermissionModel().flush_user_permission_caches(changes)

        return {
            'msg': 'Granted perm: `%s` for user: `%s` in repo: `%s`' % (
                perm.permission_name, user.username, repo.repo_name
            ),
            'success': True
        }
    except Exception:
        log.exception("Exception occurred while trying edit permissions for repo")
        raise JSONRPCError(
            'failed to edit permission for user: `%s` in repo: `%s`' % (
                userid, repoid
            )
        )


@jsonrpc_method()
def revoke_user_permission(request, apiuser, repoid, userid):
    """
    Revoke permission for a user on the specified repository.

    This command can only be run using an |authtoken| with admin
    permissions on the |repo|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Set the repository name or repository ID.
    :type repoid: str or int
    :param userid: Set the user name of revoked user.
    :type userid: str or int

    Example error output:

    .. code-block:: bash

        id : <id_given_in_input>
        result: {
                  "msg" : "Revoked perm for user: `<username>` in repo: `<reponame>`",
                  "success": true
                }
        error:  null
    """

    repo = get_repo_or_error(repoid)
    user = get_user_or_error(userid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    perm_deletions = [[user.user_id, None, "user"]]
    try:
        changes = RepoModel().update_permissions(
            repo=repo, perm_deletions=perm_deletions, cur_user=user)

        action_data = {
            'added': changes['added'],
            'updated': changes['updated'],
            'deleted': changes['deleted'],
        }
        audit_logger.store_api(
            'repo.edit.permissions', action_data=action_data, user=apiuser, repo=repo)
        Session().commit()
        PermissionModel().flush_user_permission_caches(changes)

        return {
            'msg': 'Revoked perm for user: `%s` in repo: `%s`' % (
                user.username, repo.repo_name
            ),
            'success': True
        }
    except Exception:
        log.exception("Exception occurred while trying revoke permissions to repo")
        raise JSONRPCError(
            'failed to edit permission for user: `%s` in repo: `%s`' % (
                userid, repoid
            )
        )


@jsonrpc_method()
def grant_user_group_permission(request, apiuser, repoid, usergroupid, perm):
    """
    Grant permission for a user group on the specified repository,
    or update existing permissions.

    This command can only be run using an |authtoken| with admin
    permissions on the |repo|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Set the repository name or repository ID.
    :type repoid: str or int
    :param usergroupid: Specify the ID of the user group.
    :type usergroupid: str or int
    :param perm: Set the user group permissions using the following
        format: (repository.(none|read|write|admin))
    :type perm: str

    Example output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : {
        "msg" : "Granted perm: `<perm>` for group: `<usersgroupname>` in repo: `<reponame>`",
        "success": true

      }
      error :  null

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
        "failed to edit permission for user group: `<usergroup>` in repo `<repo>`'
      }

    """

    repo = get_repo_or_error(repoid)
    perm = get_perm_or_error(perm)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    user_group = get_user_group_or_error(usergroupid)
    if not has_superadmin_permission(apiuser):
        # check if we have at least read permission for this user group !
        _perms = ('usergroup.read', 'usergroup.write', 'usergroup.admin',)
        if not HasUserGroupPermissionAnyApi(*_perms)(
                user=apiuser, user_group_name=user_group.users_group_name):
            raise JSONRPCError(
                'user group `%s` does not exist' % (usergroupid,))

    perm_additions = [[user_group.users_group_id, perm.permission_name, "user_group"]]
    try:
        changes = RepoModel().update_permissions(
            repo=repo, perm_additions=perm_additions, cur_user=apiuser)
        action_data = {
            'added': changes['added'],
            'updated': changes['updated'],
            'deleted': changes['deleted'],
        }
        audit_logger.store_api(
            'repo.edit.permissions', action_data=action_data, user=apiuser, repo=repo)
        Session().commit()
        PermissionModel().flush_user_permission_caches(changes)

        return {
            'msg': 'Granted perm: `%s` for user group: `%s` in '
                   'repo: `%s`' % (
                       perm.permission_name, user_group.users_group_name,
                       repo.repo_name
                   ),
            'success': True
        }
    except Exception:
        log.exception(
            "Exception occurred while trying change permission on repo")
        raise JSONRPCError(
            'failed to edit permission for user group: `%s` in '
            'repo: `%s`' % (
                usergroupid, repo.repo_name
            )
        )


@jsonrpc_method()
def revoke_user_group_permission(request, apiuser, repoid, usergroupid):
    """
    Revoke the permissions of a user group on a given repository.

    This command can only be run using an |authtoken| with admin
    permissions on the |repo|.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: Set the repository name or repository ID.
    :type repoid: str or int
    :param usergroupid: Specify the user group ID.
    :type usergroupid: str or int

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result: {
                  "msg" : "Revoked perm for group: `<usersgroupname>` in repo: `<reponame>`",
                  "success": true
                }
        error:  null
    """

    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    user_group = get_user_group_or_error(usergroupid)
    if not has_superadmin_permission(apiuser):
        # check if we have at least read permission for this user group !
        _perms = ('usergroup.read', 'usergroup.write', 'usergroup.admin',)
        if not HasUserGroupPermissionAnyApi(*_perms)(
                user=apiuser, user_group_name=user_group.users_group_name):
            raise JSONRPCError(
                'user group `%s` does not exist' % (usergroupid,))

    perm_deletions = [[user_group.users_group_id, None, "user_group"]]
    try:
        changes = RepoModel().update_permissions(
            repo=repo, perm_deletions=perm_deletions, cur_user=apiuser)
        action_data = {
            'added': changes['added'],
            'updated': changes['updated'],
            'deleted': changes['deleted'],
        }
        audit_logger.store_api(
            'repo.edit.permissions', action_data=action_data, user=apiuser, repo=repo)
        Session().commit()
        PermissionModel().flush_user_permission_caches(changes)

        return {
            'msg': 'Revoked perm for user group: `%s` in repo: `%s`' % (
                user_group.users_group_name, repo.repo_name
            ),
            'success': True
        }
    except Exception:
        log.exception("Exception occurred while trying revoke "
                      "user group permission on repo")
        raise JSONRPCError(
            'failed to edit permission for user group: `%s` in '
            'repo: `%s`' % (
                user_group.users_group_name, repo.repo_name
            )
        )


@jsonrpc_method()
def pull(request, apiuser, repoid, remote_uri=Optional(None)):
    """
    Triggers a pull on the given repository from a remote location. You
    can use this to keep remote repositories up-to-date.

    This command can only be run using an |authtoken| with admin
    rights to the specified repository. For more information,
    see :ref:`config-token-ref`.

    This command takes the following options:

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: The repository name or repository ID.
    :type repoid: str or int
    :param remote_uri: Optional remote URI to pass in for pull
    :type remote_uri: str

    Example output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : {
        "msg": "Pulled from url `<remote_url>` on repo `<repository name>`"
        "repository": "<repository name>"
      }
      error :  null

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
        "Unable to push changes from `<remote_url>`"
      }

    """

    repo = get_repo_or_error(repoid)
    remote_uri = Optional.extract(remote_uri)
    remote_uri_display = remote_uri or repo.clone_uri_hidden
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    try:
        ScmModel().pull_changes(
            repo.repo_name, apiuser.username, remote_uri=remote_uri)
        return {
            'msg': 'Pulled from url `%s` on repo `%s`' % (
                remote_uri_display, repo.repo_name),
            'repository': repo.repo_name
        }
    except Exception:
        log.exception("Exception occurred while trying to "
                      "pull changes from remote location")
        raise JSONRPCError(
            'Unable to pull changes from `%s`' % remote_uri_display
        )


@jsonrpc_method()
def strip(request, apiuser, repoid, revision, branch):
    """
    Strips the given revision from the specified repository.

    * This will remove the revision and all of its decendants.

    This command can only be run using an |authtoken| with admin rights to
    the specified repository.

    This command takes the following options:

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: The repository name or repository ID.
    :type repoid: str or int
    :param revision: The revision you wish to strip.
    :type revision: str
    :param branch: The branch from which to strip the revision.
    :type branch: str

    Example output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : {
        "msg": "'Stripped commit <commit_hash> from repo `<repository name>`'"
        "repository": "<repository name>"
      }
      error :  null

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
        "Unable to strip commit <commit_hash> from repo `<repository name>`"
      }

    """

    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    try:
        ScmModel().strip(repo, revision, branch)
        audit_logger.store_api(
            'repo.commit.strip', action_data={'commit_id': revision},
            repo=repo,
            user=apiuser, commit=True)

        return {
            'msg': 'Stripped commit %s from repo `%s`' % (
                revision, repo.repo_name),
            'repository': repo.repo_name
        }
    except Exception:
        log.exception("Exception while trying to strip")
        raise JSONRPCError(
            'Unable to strip commit %s from repo `%s`' % (
                revision, repo.repo_name)
        )


@jsonrpc_method()
def get_repo_settings(request, apiuser, repoid, key=Optional(None)):
    """
    Returns all settings for a repository. If key is given it only returns the
    setting identified by the key or null.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: The repository name or repository id.
    :type repoid: str or int
    :param key: Key of the setting to return.
    :type: key: Optional(str)

    Example output:

    .. code-block:: bash

        {
            "error": null,
            "id": 237,
            "result": {
                "extensions_largefiles": true,
                "extensions_evolve": true,
                "hooks_changegroup_push_logger": true,
                "hooks_changegroup_repo_size": false,
                "hooks_outgoing_pull_logger": true,
                "phases_publish": "True",
                "rhodecode_hg_use_rebase_for_merging": true,
                "rhodecode_pr_merge_enabled": true,
                "rhodecode_use_outdated_comments": true
            }
        }
    """

    # Restrict access to this api method to super-admins, and repo admins only.
    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    try:
        settings_model = VcsSettingsModel(repo=repo)
        settings = settings_model.get_global_settings()
        settings.update(settings_model.get_repo_settings())

        # If only a single setting is requested fetch it from all settings.
        key = Optional.extract(key)
        if key is not None:
            settings = settings.get(key, None)
    except Exception:
        msg = 'Failed to fetch settings for repository `{}`'.format(repoid)
        log.exception(msg)
        raise JSONRPCError(msg)

    return settings


@jsonrpc_method()
def set_repo_settings(request, apiuser, repoid, settings):
    """
    Update repository settings. Returns true on success.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: The repository name or repository id.
    :type repoid: str or int
    :param settings: The new settings for the repository.
    :type: settings: dict

    Example output:

    .. code-block:: bash

        {
            "error": null,
            "id": 237,
            "result": true
        }
    """
    # Restrict access to this api method to super-admins, and repo admins only.
    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    if type(settings) is not dict:
        raise JSONRPCError('Settings have to be a JSON Object.')

    try:
        settings_model = VcsSettingsModel(repo=repoid)

        # Merge global, repo and incoming settings.
        new_settings = settings_model.get_global_settings()
        new_settings.update(settings_model.get_repo_settings())
        new_settings.update(settings)

        # Update the settings.
        inherit_global_settings = new_settings.get(
            'inherit_global_settings', False)
        settings_model.create_or_update_repo_settings(
            new_settings, inherit_global_settings=inherit_global_settings)
        Session().commit()
    except Exception:
        msg = 'Failed to update settings for repository `{}`'.format(repoid)
        log.exception(msg)
        raise JSONRPCError(msg)

    # Indicate success.
    return True


@jsonrpc_method()
def maintenance(request, apiuser, repoid):
    """
    Triggers a maintenance on the given repository.

    This command can only be run using an |authtoken| with admin
    rights to the specified repository. For more information,
    see :ref:`config-token-ref`.

    This command takes the following options:

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repoid: The repository name or repository ID.
    :type repoid: str or int

    Example output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : {
        "msg": "executed maintenance command",
        "executed_actions": [
           <action_message>, <action_message2>...
        ],
        "repository": "<repository name>"
      }
      error :  null

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
        "Unable to execute maintenance on `<reponame>`"
      }

    """

    repo = get_repo_or_error(repoid)
    if not has_superadmin_permission(apiuser):
        _perms = ('repository.admin',)
        validate_repo_permissions(apiuser, repoid, repo, _perms)

    try:
        maintenance = repo_maintenance.RepoMaintenance()
        executed_actions = maintenance.execute(repo)

        return {
            'msg': 'executed maintenance command',
            'executed_actions': executed_actions,
            'repository': repo.repo_name
        }
    except Exception:
        log.exception("Exception occurred while trying to run maintenance")
        raise JSONRPCError(
            'Unable to execute maintenance on `%s`' % repo.repo_name)
