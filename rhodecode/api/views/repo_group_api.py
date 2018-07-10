# -*- coding: utf-8 -*-

# Copyright (C) 2011-2018 RhodeCode GmbH
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

from rhodecode.api import JSONRPCValidationError
from rhodecode.api import jsonrpc_method, JSONRPCError
from rhodecode.api.utils import (
    has_superadmin_permission, Optional, OAttr, get_user_or_error,
    get_repo_group_or_error, get_perm_or_error, get_user_group_or_error,
    get_origin, validate_repo_group_permissions, validate_set_owner_permissions)
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import (
    HasRepoGroupPermissionAnyApi, HasUserGroupPermissionAnyApi)
from rhodecode.model.db import Session
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.scm import RepoGroupList
from rhodecode.model import validation_schema
from rhodecode.model.validation_schema.schemas import repo_group_schema


log = logging.getLogger(__name__)


@jsonrpc_method()
def get_repo_group(request, apiuser, repogroupid):
    """
    Return the specified |repo| group, along with permissions,
    and repositories inside the group

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repogroupid: Specify the name of ID of the repository group.
    :type repogroupid: str or int


    Example output:

    .. code-block:: bash

        {
          "error": null,
          "id": repo-group-id,
          "result": {
            "group_description": "repo group description",
            "group_id": 14,
            "group_name": "group name",
            "permissions": [
              {
                "name": "super-admin-username",
                "origin": "super-admin",
                "permission": "group.admin",
                "type": "user"
              },
              {
                "name": "owner-name",
                "origin": "owner",
                "permission": "group.admin",
                "type": "user"
              },
              {
                "name": "user-group-name",
                "origin": "permission",
                "permission": "group.write",
                "type": "user_group"
              }
            ],
            "owner": "owner-name",
            "parent_group": null,
            "repositories": [ repo-list ]
          }
        }
    """

    repo_group = get_repo_group_or_error(repogroupid)
    if not has_superadmin_permission(apiuser):
        # check if we have at least read permission for this repo group !
        _perms = ('group.admin', 'group.write', 'group.read',)
        if not HasRepoGroupPermissionAnyApi(*_perms)(
                user=apiuser, group_name=repo_group.group_name):
            raise JSONRPCError(
                'repository group `%s` does not exist' % (repogroupid,))

    permissions = []
    for _user in repo_group.permissions():
        user_data = {
            'name': _user.username,
            'permission': _user.permission,
            'origin': get_origin(_user),
            'type': "user",
        }
        permissions.append(user_data)

    for _user_group in repo_group.permission_user_groups():
        user_group_data = {
            'name': _user_group.users_group_name,
            'permission': _user_group.permission,
            'origin': get_origin(_user_group),
            'type': "user_group",
        }
        permissions.append(user_group_data)

    data = repo_group.get_api_data()
    data["permissions"] = permissions
    return data


@jsonrpc_method()
def get_repo_groups(request, apiuser):
    """
    Returns all repository groups.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    """

    result = []
    _perms = ('group.read', 'group.write', 'group.admin',)
    extras = {'user': apiuser}
    for repo_group in RepoGroupList(RepoGroupModel().get_all(),
                                    perm_set=_perms, extra_kwargs=extras):
        result.append(repo_group.get_api_data())
    return result


@jsonrpc_method()
def create_repo_group(
        request, apiuser, group_name,
        owner=Optional(OAttr('apiuser')),
        description=Optional(''),
        copy_permissions=Optional(False)):
    """
    Creates a repository group.

    * If the repository group name contains "/", repository group will be
      created inside a repository group or nested repository groups

      For example "foo/bar/group1" will create repository group called "group1"
      inside group "foo/bar". You have to have permissions to access and
      write to the last repository group ("bar" in this example)

    This command can only be run using an |authtoken| with at least
    permissions to create repository groups, or admin permissions to
    parent repository groups.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param group_name: Set the repository group name.
    :type group_name: str
    :param description: Set the |repo| group description.
    :type description: str
    :param owner: Set the |repo| group owner.
    :type owner: str
    :param copy_permissions:
    :type copy_permissions:

    Example output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : {
          "msg": "Created new repo group `<repo_group_name>`"
          "repo_group": <repogroup_object>
      }
      error :  null


    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
        failed to create repo group `<repogroupid>`
      }

    """

    owner = validate_set_owner_permissions(apiuser, owner)

    description = Optional.extract(description)
    copy_permissions = Optional.extract(copy_permissions)

    schema = repo_group_schema.RepoGroupSchema().bind(
        # user caller
        user=apiuser)

    try:
        schema_data = schema.deserialize(dict(
            repo_group_name=group_name,
            repo_group_owner=owner.username,
            repo_group_description=description,
            repo_group_copy_permissions=copy_permissions,
        ))
    except validation_schema.Invalid as err:
        raise JSONRPCValidationError(colander_exc=err)

    validated_group_name = schema_data['repo_group_name']

    try:
        repo_group = RepoGroupModel().create(
            owner=owner,
            group_name=validated_group_name,
            group_description=schema_data['repo_group_description'],
            copy_permissions=schema_data['repo_group_copy_permissions'])
        Session().flush()

        repo_group_data = repo_group.get_api_data()
        audit_logger.store_api(
            'repo_group.create', action_data={'data': repo_group_data},
            user=apiuser)

        Session().commit()
        return {
            'msg': 'Created new repo group `%s`' % validated_group_name,
            'repo_group': repo_group.get_api_data()
        }
    except Exception:
        log.exception("Exception occurred while trying create repo group")
        raise JSONRPCError(
            'failed to create repo group `%s`' % (validated_group_name,))


@jsonrpc_method()
def update_repo_group(
        request, apiuser, repogroupid, group_name=Optional(''),
        description=Optional(''), owner=Optional(OAttr('apiuser')),
        enable_locking=Optional(False)):
    """
    Updates repository group with the details given.

    This command can only be run using an |authtoken| with admin
    permissions.

    * If the group_name name contains "/", repository group will be updated
      accordingly with a repository group or nested repository groups

      For example repogroupid=group-test group_name="foo/bar/group-test"
      will update repository group called "group-test" and place it
      inside group "foo/bar".
      You have to have permissions to access and write to the last repository
      group ("bar" in this example)

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repogroupid: Set the ID of repository group.
    :type repogroupid: str or int
    :param group_name: Set the name of the |repo| group.
    :type group_name: str
    :param description: Set a description for the group.
    :type description: str
    :param owner: Set the |repo| group owner.
    :type owner: str
    :param enable_locking: Enable |repo| locking. The default is false.
    :type enable_locking: bool
    """

    repo_group = get_repo_group_or_error(repogroupid)

    if not has_superadmin_permission(apiuser):
        validate_repo_group_permissions(
            apiuser, repogroupid, repo_group, ('group.admin',))

    updates = dict(
        group_name=group_name
        if not isinstance(group_name, Optional) else repo_group.group_name,

        group_description=description
        if not isinstance(description, Optional) else repo_group.group_description,

        user=owner
        if not isinstance(owner, Optional) else repo_group.user.username,

        enable_locking=enable_locking
        if not isinstance(enable_locking, Optional) else repo_group.enable_locking
    )

    schema = repo_group_schema.RepoGroupSchema().bind(
        # user caller
        user=apiuser,
        old_values=repo_group.get_api_data())

    try:
        schema_data = schema.deserialize(dict(
            repo_group_name=updates['group_name'],
            repo_group_owner=updates['user'],
            repo_group_description=updates['group_description'],
            repo_group_enable_locking=updates['enable_locking'],
        ))
    except validation_schema.Invalid as err:
        raise JSONRPCValidationError(colander_exc=err)

    validated_updates = dict(
        group_name=schema_data['repo_group']['repo_group_name_without_group'],
        group_parent_id=schema_data['repo_group']['repo_group_id'],
        user=schema_data['repo_group_owner'],
        group_description=schema_data['repo_group_description'],
        enable_locking=schema_data['repo_group_enable_locking'],
    )

    old_data = repo_group.get_api_data()
    try:
        RepoGroupModel().update(repo_group, validated_updates)
        audit_logger.store_api(
            'repo_group.edit', action_data={'old_data': old_data},
            user=apiuser)

        Session().commit()
        return {
            'msg': 'updated repository group ID:%s %s' % (
                repo_group.group_id, repo_group.group_name),
            'repo_group': repo_group.get_api_data()
        }
    except Exception:
        log.exception(
            u"Exception occurred while trying update repo group %s",
            repogroupid)
        raise JSONRPCError('failed to update repository group `%s`'
                           % (repogroupid,))


@jsonrpc_method()
def delete_repo_group(request, apiuser, repogroupid):
    """
    Deletes a |repo| group.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repogroupid: Set the name or ID of repository group to be
        deleted.
    :type repogroupid: str or int

    Example output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : {
        'msg': 'deleted repo group ID:<repogroupid> <repogroupname>'
        'repo_group': null
      }
      error :  null

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
        "failed to delete repo group ID:<repogroupid> <repogroupname>"
      }

    """

    repo_group = get_repo_group_or_error(repogroupid)
    if not has_superadmin_permission(apiuser):
        validate_repo_group_permissions(
            apiuser, repogroupid, repo_group, ('group.admin',))

    old_data = repo_group.get_api_data()
    try:
        RepoGroupModel().delete(repo_group)
        audit_logger.store_api(
            'repo_group.delete', action_data={'old_data': old_data},
            user=apiuser)
        Session().commit()
        return {
            'msg': 'deleted repo group ID:%s %s' %
                   (repo_group.group_id, repo_group.group_name),
            'repo_group': None
        }
    except Exception:
        log.exception("Exception occurred while trying to delete repo group")
        raise JSONRPCError('failed to delete repo group ID:%s %s' %
                           (repo_group.group_id, repo_group.group_name))


@jsonrpc_method()
def grant_user_permission_to_repo_group(
        request, apiuser, repogroupid, userid, perm,
        apply_to_children=Optional('none')):
    """
    Grant permission for a user on the given repository group, or update
    existing permissions if found.

    This command can only be run using an |authtoken| with admin
    permissions.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repogroupid: Set the name or ID of repository group.
    :type repogroupid: str or int
    :param userid: Set the user name.
    :type userid: str
    :param perm: (group.(none|read|write|admin))
    :type perm: str
    :param apply_to_children: 'none', 'repos', 'groups', 'all'
    :type apply_to_children: str

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result: {
                  "msg" : "Granted perm: `<perm>` (recursive:<apply_to_children>) for user: `<username>` in repo group: `<repo_group_name>`",
                  "success": true
                }
        error:  null

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
        "failed to edit permission for user: `<userid>` in repo group: `<repo_group_name>`"
      }

    """

    repo_group = get_repo_group_or_error(repogroupid)

    if not has_superadmin_permission(apiuser):
        validate_repo_group_permissions(
            apiuser, repogroupid, repo_group, ('group.admin',))

    user = get_user_or_error(userid)
    perm = get_perm_or_error(perm, prefix='group.')
    apply_to_children = Optional.extract(apply_to_children)

    perm_additions = [[user.user_id, perm.permission_name, "user"]]
    try:
        RepoGroupModel().update_permissions(repo_group=repo_group,
                                            perm_additions=perm_additions,
                                            recursive=apply_to_children,
                                            cur_user=apiuser)
        Session().commit()
        return {
            'msg': 'Granted perm: `%s` (recursive:%s) for user: '
                   '`%s` in repo group: `%s`' % (
                       perm.permission_name, apply_to_children, user.username,
                       repo_group.name
                   ),
            'success': True
        }
    except Exception:
        log.exception("Exception occurred while trying to grant "
                      "user permissions to repo group")
        raise JSONRPCError(
            'failed to edit permission for user: '
            '`%s` in repo group: `%s`' % (userid, repo_group.name))


@jsonrpc_method()
def revoke_user_permission_from_repo_group(
        request, apiuser, repogroupid, userid,
        apply_to_children=Optional('none')):
    """
    Revoke permission for a user in a given repository group.

    This command can only be run using an |authtoken| with admin
    permissions on the |repo| group.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repogroupid: Set the name or ID of the repository group.
    :type repogroupid: str or int
    :param userid: Set the user name to revoke.
    :type userid: str
    :param apply_to_children: 'none', 'repos', 'groups', 'all'
    :type apply_to_children: str

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result: {
                  "msg" : "Revoked perm (recursive:<apply_to_children>) for user: `<username>` in repo group: `<repo_group_name>`",
                  "success": true
                }
        error:  null

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
        "failed to edit permission for user: `<userid>` in repo group: `<repo_group_name>`"
      }

    """

    repo_group = get_repo_group_or_error(repogroupid)

    if not has_superadmin_permission(apiuser):
        validate_repo_group_permissions(
            apiuser, repogroupid, repo_group, ('group.admin',))

    user = get_user_or_error(userid)
    apply_to_children = Optional.extract(apply_to_children)

    perm_deletions = [[user.user_id, None, "user"]]
    try:
        RepoGroupModel().update_permissions(repo_group=repo_group,
                                            perm_deletions=perm_deletions,
                                            recursive=apply_to_children,
                                            cur_user=apiuser)
        Session().commit()
        return {
            'msg': 'Revoked perm (recursive:%s) for user: '
                   '`%s` in repo group: `%s`' % (
                       apply_to_children, user.username, repo_group.name
                   ),
            'success': True
        }
    except Exception:
        log.exception("Exception occurred while trying revoke user "
                      "permission from repo group")
        raise JSONRPCError(
            'failed to edit permission for user: '
            '`%s` in repo group: `%s`' % (userid, repo_group.name))


@jsonrpc_method()
def grant_user_group_permission_to_repo_group(
        request, apiuser, repogroupid, usergroupid, perm,
        apply_to_children=Optional('none'), ):
    """
    Grant permission for a user group on given repository group, or update
    existing permissions if found.

    This command can only be run using an |authtoken| with admin
    permissions on the |repo| group.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repogroupid: Set the name or id of repository group
    :type repogroupid: str or int
    :param usergroupid: id of usergroup
    :type usergroupid: str or int
    :param perm: (group.(none|read|write|admin))
    :type perm: str
    :param apply_to_children: 'none', 'repos', 'groups', 'all'
    :type apply_to_children: str

    Example output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : {
        "msg" : "Granted perm: `<perm>` (recursive:<apply_to_children>) for user group: `<usersgroupname>` in repo group: `<repo_group_name>`",
        "success": true

      }
      error :  null

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
        "failed to edit permission for user group: `<usergroup>` in repo group: `<repo_group_name>`"
      }

    """

    repo_group = get_repo_group_or_error(repogroupid)
    perm = get_perm_or_error(perm, prefix='group.')
    user_group = get_user_group_or_error(usergroupid)
    if not has_superadmin_permission(apiuser):
        validate_repo_group_permissions(
            apiuser, repogroupid, repo_group, ('group.admin',))

        # check if we have at least read permission for this user group !
        _perms = ('usergroup.read', 'usergroup.write', 'usergroup.admin',)
        if not HasUserGroupPermissionAnyApi(*_perms)(
                user=apiuser, user_group_name=user_group.users_group_name):
            raise JSONRPCError(
                'user group `%s` does not exist' % (usergroupid,))

    apply_to_children = Optional.extract(apply_to_children)

    perm_additions = [[user_group.users_group_id, perm.permission_name, "user_group"]]
    try:
        RepoGroupModel().update_permissions(repo_group=repo_group,
                                            perm_additions=perm_additions,
                                            recursive=apply_to_children,
                                            cur_user=apiuser)
        Session().commit()
        return {
            'msg': 'Granted perm: `%s` (recursive:%s) '
                   'for user group: `%s` in repo group: `%s`' % (
                       perm.permission_name, apply_to_children,
                       user_group.users_group_name, repo_group.name
                   ),
            'success': True
        }
    except Exception:
        log.exception("Exception occurred while trying to grant user "
                      "group permissions to repo group")
        raise JSONRPCError(
            'failed to edit permission for user group: `%s` in '
            'repo group: `%s`' % (
                usergroupid, repo_group.name
            )
        )


@jsonrpc_method()
def revoke_user_group_permission_from_repo_group(
        request, apiuser, repogroupid, usergroupid,
        apply_to_children=Optional('none')):
    """
    Revoke permission for user group on given repository.

    This command can only be run using an |authtoken| with admin
    permissions on the |repo| group.

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param repogroupid: name or id of repository group
    :type repogroupid: str or int
    :param usergroupid:
    :param apply_to_children: 'none', 'repos', 'groups', 'all'
    :type apply_to_children: str

    Example output:

    .. code-block:: bash

        id : <id_given_in_input>
        result: {
                  "msg" : "Revoked perm (recursive:<apply_to_children>) for user group: `<usersgroupname>` in repo group: `<repo_group_name>`",
                  "success": true
                }
        error:  null

    Example error output:

    .. code-block:: bash

      id : <id_given_in_input>
      result : null
      error :  {
        "failed to edit permission for user group: `<usergroup>` in repo group: `<repo_group_name>`"
      }


    """

    repo_group = get_repo_group_or_error(repogroupid)
    user_group = get_user_group_or_error(usergroupid)
    if not has_superadmin_permission(apiuser):
        validate_repo_group_permissions(
            apiuser, repogroupid, repo_group, ('group.admin',))

        # check if we have at least read permission for this user group !
        _perms = ('usergroup.read', 'usergroup.write', 'usergroup.admin',)
        if not HasUserGroupPermissionAnyApi(*_perms)(
                user=apiuser, user_group_name=user_group.users_group_name):
            raise JSONRPCError(
                'user group `%s` does not exist' % (usergroupid,))

    apply_to_children = Optional.extract(apply_to_children)

    perm_deletions = [[user_group.users_group_id, None, "user_group"]]
    try:
        RepoGroupModel().update_permissions(repo_group=repo_group,
                                            perm_deletions=perm_deletions,
                                            recursive=apply_to_children,
                                            cur_user=apiuser)
        Session().commit()
        return {
            'msg': 'Revoked perm (recursive:%s) for user group: '
                   '`%s` in repo group: `%s`' % (
                       apply_to_children, user_group.users_group_name,
                       repo_group.name
                   ),
            'success': True
        }
    except Exception:
        log.exception("Exception occurred while trying revoke user group "
                      "permissions from repo group")
        raise JSONRPCError(
            'failed to edit permission for user group: '
            '`%s` in repo group: `%s`' % (
                user_group.users_group_name, repo_group.name
            )
        )

