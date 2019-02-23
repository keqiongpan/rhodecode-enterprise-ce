# -*- coding: utf-8 -*-

# Copyright (C) 2011-2019 RhodeCode GmbH
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
import traceback
from pyramid import compat

from rhodecode.lib.utils2 import safe_str, safe_unicode
from rhodecode.lib.exceptions import (
    UserGroupAssignedException, RepoGroupAssignmentError)
from rhodecode.lib.utils2 import (
    get_current_rhodecode_user, action_logger_generic)
from rhodecode.model import BaseModel
from rhodecode.model.scm import UserGroupList
from rhodecode.model.db import (
    joinedload, true, func, User, UserGroupMember, UserGroup,
    UserGroupRepoToPerm, Permission, UserGroupToPerm, UserUserGroupToPerm,
    UserGroupUserGroupToPerm, UserGroupRepoGroupToPerm)


log = logging.getLogger(__name__)


class UserGroupModel(BaseModel):

    cls = UserGroup

    def _get_user_group(self, user_group):
        return self._get_instance(UserGroup, user_group,
                                  callback=UserGroup.get_by_group_name)

    def _create_default_perms(self, user_group):
        # create default permission
        default_perm = 'usergroup.read'
        def_user = User.get_default_user()
        for p in def_user.user_perms:
            if p.permission.permission_name.startswith('usergroup.'):
                default_perm = p.permission.permission_name
                break

        user_group_to_perm = UserUserGroupToPerm()
        user_group_to_perm.permission = Permission.get_by_key(default_perm)

        user_group_to_perm.user_group = user_group
        user_group_to_perm.user_id = def_user.user_id
        return user_group_to_perm

    def update_permissions(
            self, user_group, perm_additions=None, perm_updates=None,
            perm_deletions=None, check_perms=True, cur_user=None):

        from rhodecode.lib.auth import HasUserGroupPermissionAny
        if not perm_additions:
            perm_additions = []
        if not perm_updates:
            perm_updates = []
        if not perm_deletions:
            perm_deletions = []

        req_perms = ('usergroup.read', 'usergroup.write', 'usergroup.admin')

        changes = {
            'added': [],
            'updated': [],
            'deleted': []
        }
        change_obj = user_group.get_api_data()
        # update permissions
        for member_id, perm, member_type in perm_updates:
            member_id = int(member_id)
            if member_type == 'user':
                member_name = User.get(member_id).username
                # this updates existing one
                self.grant_user_permission(
                    user_group=user_group, user=member_id, perm=perm
                )
            elif member_type == 'user_group':
                # check if we have permissions to alter this usergroup
                member_name = UserGroup.get(member_id).users_group_name
                if not check_perms or HasUserGroupPermissionAny(
                        *req_perms)(member_name, user=cur_user):
                    self.grant_user_group_permission(
                        target_user_group=user_group, user_group=member_id, perm=perm)
            else:
                raise ValueError("member_type must be 'user' or 'user_group' "
                                 "got {} instead".format(member_type))

            changes['updated'].append({
                'change_obj': change_obj,
                'type': member_type, 'id': member_id,
                'name': member_name, 'new_perm': perm})

        # set new permissions
        for member_id, perm, member_type in perm_additions:
            member_id = int(member_id)
            if member_type == 'user':
                member_name = User.get(member_id).username
                self.grant_user_permission(
                    user_group=user_group, user=member_id, perm=perm)
            elif member_type == 'user_group':
                # check if we have permissions to alter this usergroup
                member_name = UserGroup.get(member_id).users_group_name
                if not check_perms or HasUserGroupPermissionAny(
                        *req_perms)(member_name, user=cur_user):
                    self.grant_user_group_permission(
                        target_user_group=user_group, user_group=member_id, perm=perm)
            else:
                raise ValueError("member_type must be 'user' or 'user_group' "
                                 "got {} instead".format(member_type))

            changes['added'].append({
                'change_obj': change_obj,
                'type': member_type, 'id': member_id,
                'name': member_name, 'new_perm': perm})

        # delete permissions
        for member_id, perm, member_type in perm_deletions:
            member_id = int(member_id)
            if member_type == 'user':
                member_name = User.get(member_id).username
                self.revoke_user_permission(user_group=user_group, user=member_id)
            elif member_type == 'user_group':
                # check if we have permissions to alter this usergroup
                member_name = UserGroup.get(member_id).users_group_name
                if not check_perms or HasUserGroupPermissionAny(
                        *req_perms)(member_name, user=cur_user):
                    self.revoke_user_group_permission(
                        target_user_group=user_group, user_group=member_id)
            else:
                raise ValueError("member_type must be 'user' or 'user_group' "
                                 "got {} instead".format(member_type))

            changes['deleted'].append({
                'change_obj': change_obj,
                'type': member_type, 'id': member_id,
                'name': member_name, 'new_perm': perm})

        return changes

    def get(self, user_group_id, cache=False):
        return UserGroup.get(user_group_id)

    def get_group(self, user_group):
        return self._get_user_group(user_group)

    def get_by_name(self, name, cache=False, case_insensitive=False):
        return UserGroup.get_by_group_name(name, cache, case_insensitive)

    def create(self, name, description, owner, active=True, group_data=None):
        try:
            new_user_group = UserGroup()
            new_user_group.user = self._get_user(owner)
            new_user_group.users_group_name = name
            new_user_group.user_group_description = description
            new_user_group.users_group_active = active
            if group_data:
                new_user_group.group_data = group_data
            self.sa.add(new_user_group)
            perm_obj = self._create_default_perms(new_user_group)
            self.sa.add(perm_obj)

            self.grant_user_permission(user_group=new_user_group,
                                       user=owner, perm='usergroup.admin')

            return new_user_group
        except Exception:
            log.error(traceback.format_exc())
            raise

    def _get_memberships_for_user_ids(self, user_group, user_id_list):
        members = []
        for user_id in user_id_list:
            member = self._get_membership(user_group.users_group_id, user_id)
            members.append(member)
        return members

    def _get_added_and_removed_user_ids(self, user_group, user_id_list):
        current_members = user_group.members or []
        current_members_ids = [m.user.user_id for m in current_members]

        added_members = [
            user_id for user_id in user_id_list
            if user_id not in current_members_ids]
        if user_id_list == []:
            # all members were deleted
            deleted_members = current_members_ids
        else:
            deleted_members = [
                user_id for user_id in current_members_ids
                if user_id not in user_id_list]

        return added_members, deleted_members

    def _set_users_as_members(self, user_group, user_ids):
        user_group.members = []
        self.sa.flush()
        members = self._get_memberships_for_user_ids(
            user_group, user_ids)
        user_group.members = members
        self.sa.add(user_group)

    def _update_members_from_user_ids(self, user_group, user_ids):
        added, removed = self._get_added_and_removed_user_ids(
            user_group, user_ids)
        self._set_users_as_members(user_group, user_ids)
        self._log_user_changes('added to', user_group, added)
        self._log_user_changes('removed from', user_group, removed)
        return added, removed

    def _clean_members_data(self, members_data):
        if not members_data:
            members_data = []

        members = []
        for user in members_data:
            uid = int(user['member_user_id'])
            if uid not in members and user['type'] in ['new', 'existing']:
                members.append(uid)
        return members

    def update(self, user_group, form_data, group_data=None):
        user_group = self._get_user_group(user_group)
        if 'users_group_name' in form_data:
            user_group.users_group_name = form_data['users_group_name']
        if 'users_group_active' in form_data:
            user_group.users_group_active = form_data['users_group_active']
        if 'user_group_description' in form_data:
            user_group.user_group_description = form_data[
                'user_group_description']

        # handle owner change
        if 'user' in form_data:
            owner = form_data['user']
            if isinstance(owner, compat.string_types):
                owner = User.get_by_username(form_data['user'])

            if not isinstance(owner, User):
                raise ValueError(
                    'invalid owner for user group: %s' % form_data['user'])

            user_group.user = owner

        added_user_ids = []
        removed_user_ids = []
        if 'users_group_members' in form_data:
            members_id_list = self._clean_members_data(
                form_data['users_group_members'])
            added_user_ids, removed_user_ids = \
                self._update_members_from_user_ids(user_group, members_id_list)

        if group_data:
            new_group_data = {}
            new_group_data.update(group_data)
            user_group.group_data = new_group_data

        self.sa.add(user_group)
        return user_group, added_user_ids, removed_user_ids

    def delete(self, user_group, force=False):
        """
        Deletes repository group, unless force flag is used
        raises exception if there are members in that group, else deletes
        group and users

        :param user_group:
        :param force:
        """
        user_group = self._get_user_group(user_group)
        if not user_group:
            return

        try:
            # check if this group is not assigned to repo
            assigned_to_repo = [x.repository for x in UserGroupRepoToPerm.query()\
                .filter(UserGroupRepoToPerm.users_group == user_group).all()]
            # check if this group is not assigned to repo
            assigned_to_repo_group = [x.group for x in UserGroupRepoGroupToPerm.query()\
                .filter(UserGroupRepoGroupToPerm.users_group == user_group).all()]

            if (assigned_to_repo or assigned_to_repo_group) and not force:
                assigned = ','.join(map(safe_str,
                                    assigned_to_repo+assigned_to_repo_group))

                raise UserGroupAssignedException(
                    'UserGroup assigned to %s' % (assigned,))
            self.sa.delete(user_group)
        except Exception:
            log.error(traceback.format_exc())
            raise

    def _log_user_changes(self, action, user_group, user_or_users):
        users = user_or_users
        if not isinstance(users, (list, tuple)):
            users = [users]

        group_name = user_group.users_group_name

        for user_or_user_id in users:
            user = self._get_user(user_or_user_id)
            log_text = 'User {user} {action} {group}'.format(
                action=action, user=user.username, group=group_name)
            action_logger_generic(log_text)

    def _find_user_in_group(self, user, user_group):
        user_group_member = None
        for m in user_group.members:
            if m.user_id == user.user_id:
                # Found this user's membership row
                user_group_member = m
                break

        return user_group_member

    def _get_membership(self, user_group_id, user_id):
        user_group_member = UserGroupMember(user_group_id, user_id)
        return user_group_member

    def add_user_to_group(self, user_group, user):
        user_group = self._get_user_group(user_group)
        user = self._get_user(user)
        user_member = self._find_user_in_group(user, user_group)
        if user_member:
            # user already in the group, skip
            return True

        member = self._get_membership(
            user_group.users_group_id, user.user_id)
        user_group.members.append(member)

        try:
            self.sa.add(member)
        except Exception:
            # what could go wrong here?
            log.error(traceback.format_exc())
            raise

        self._log_user_changes('added to', user_group, user)
        return member

    def remove_user_from_group(self, user_group, user):
        user_group = self._get_user_group(user_group)
        user = self._get_user(user)
        user_group_member = self._find_user_in_group(user, user_group)

        if not user_group_member:
            # User isn't in that group
            return False

        try:
            self.sa.delete(user_group_member)
        except Exception:
            log.error(traceback.format_exc())
            raise

        self._log_user_changes('removed from', user_group, user)
        return True

    def has_perm(self, user_group, perm):
        user_group = self._get_user_group(user_group)
        perm = self._get_perm(perm)

        return UserGroupToPerm.query()\
            .filter(UserGroupToPerm.users_group == user_group)\
            .filter(UserGroupToPerm.permission == perm).scalar() is not None

    def grant_perm(self, user_group, perm):
        user_group = self._get_user_group(user_group)
        perm = self._get_perm(perm)

        # if this permission is already granted skip it
        _perm = UserGroupToPerm.query()\
            .filter(UserGroupToPerm.users_group == user_group)\
            .filter(UserGroupToPerm.permission == perm)\
            .scalar()
        if _perm:
            return

        new = UserGroupToPerm()
        new.users_group = user_group
        new.permission = perm
        self.sa.add(new)
        return new

    def revoke_perm(self, user_group, perm):
        user_group = self._get_user_group(user_group)
        perm = self._get_perm(perm)

        obj = UserGroupToPerm.query()\
            .filter(UserGroupToPerm.users_group == user_group)\
            .filter(UserGroupToPerm.permission == perm).scalar()
        if obj:
            self.sa.delete(obj)

    def grant_user_permission(self, user_group, user, perm):
        """
        Grant permission for user on given user group, or update
        existing one if found

        :param user_group: Instance of UserGroup, users_group_id,
            or users_group_name
        :param user: Instance of User, user_id or username
        :param perm: Instance of Permission, or permission_name
        """
        changes = {
            'added': [],
            'updated': [],
            'deleted': []
        }

        user_group = self._get_user_group(user_group)
        user = self._get_user(user)
        permission = self._get_perm(perm)
        perm_name = permission.permission_name
        member_id = user.user_id
        member_name = user.username

        # check if we have that permission already
        obj = self.sa.query(UserUserGroupToPerm)\
            .filter(UserUserGroupToPerm.user == user)\
            .filter(UserUserGroupToPerm.user_group == user_group)\
            .scalar()
        if obj is None:
            # create new !
            obj = UserUserGroupToPerm()
        obj.user_group = user_group
        obj.user = user
        obj.permission = permission
        self.sa.add(obj)
        log.debug('Granted perm %s to %s on %s', perm, user, user_group)
        action_logger_generic(
            'granted permission: {} to user: {} on usergroup: {}'.format(
                perm, user, user_group), namespace='security.usergroup')

        changes['added'].append({
            'change_obj': user_group.get_api_data(),
            'type': 'user', 'id': member_id,
            'name': member_name, 'new_perm': perm_name})

        return changes

    def revoke_user_permission(self, user_group, user):
        """
        Revoke permission for user on given user group

        :param user_group: Instance of UserGroup, users_group_id,
            or users_group name
        :param user: Instance of User, user_id or username
        """
        changes = {
            'added': [],
            'updated': [],
            'deleted': []
        }

        user_group = self._get_user_group(user_group)
        user = self._get_user(user)
        perm_name = 'usergroup.none'
        member_id = user.user_id
        member_name = user.username

        obj = self.sa.query(UserUserGroupToPerm)\
            .filter(UserUserGroupToPerm.user == user)\
            .filter(UserUserGroupToPerm.user_group == user_group)\
            .scalar()
        if obj:
            self.sa.delete(obj)
            log.debug('Revoked perm on %s on %s', user_group, user)
            action_logger_generic(
                'revoked permission from user: {} on usergroup: {}'.format(
                    user, user_group), namespace='security.usergroup')

            changes['deleted'].append({
                'change_obj': user_group.get_api_data(),
                'type': 'user', 'id': member_id,
                'name': member_name, 'new_perm': perm_name})

        return changes

    def grant_user_group_permission(self, target_user_group, user_group, perm):
        """
        Grant user group permission for given target_user_group

        :param target_user_group:
        :param user_group:
        :param perm:
        """
        changes = {
            'added': [],
            'updated': [],
            'deleted': []
        }

        target_user_group = self._get_user_group(target_user_group)
        user_group = self._get_user_group(user_group)
        permission = self._get_perm(perm)
        perm_name = permission.permission_name
        member_id = user_group.users_group_id
        member_name = user_group.users_group_name

        # forbid assigning same user group to itself
        if target_user_group == user_group:
            raise RepoGroupAssignmentError('target repo:%s cannot be '
                                           'assigned to itself' % target_user_group)

        # check if we have that permission already
        obj = self.sa.query(UserGroupUserGroupToPerm)\
            .filter(UserGroupUserGroupToPerm.target_user_group == target_user_group)\
            .filter(UserGroupUserGroupToPerm.user_group == user_group)\
            .scalar()
        if obj is None:
            # create new !
            obj = UserGroupUserGroupToPerm()
        obj.user_group = user_group
        obj.target_user_group = target_user_group
        obj.permission = permission
        self.sa.add(obj)
        log.debug(
            'Granted perm %s to %s on %s', perm, target_user_group, user_group)
        action_logger_generic(
            'granted permission: {} to usergroup: {} on usergroup: {}'.format(
                perm, user_group, target_user_group),
            namespace='security.usergroup')

        changes['added'].append({
            'change_obj': target_user_group.get_api_data(),
            'type': 'user_group', 'id': member_id,
            'name': member_name, 'new_perm': perm_name})

        return changes

    def revoke_user_group_permission(self, target_user_group, user_group):
        """
        Revoke user group permission for given target_user_group

        :param target_user_group:
        :param user_group:
        """
        changes = {
            'added': [],
            'updated': [],
            'deleted': []
        }

        target_user_group = self._get_user_group(target_user_group)
        user_group = self._get_user_group(user_group)
        perm_name = 'usergroup.none'
        member_id = user_group.users_group_id
        member_name = user_group.users_group_name

        obj = self.sa.query(UserGroupUserGroupToPerm)\
            .filter(UserGroupUserGroupToPerm.target_user_group == target_user_group)\
            .filter(UserGroupUserGroupToPerm.user_group == user_group)\
            .scalar()
        if obj:
            self.sa.delete(obj)
            log.debug(
                'Revoked perm on %s on %s', target_user_group, user_group)
            action_logger_generic(
                'revoked permission from usergroup: {} on usergroup: {}'.format(
                    user_group, target_user_group),
                namespace='security.repogroup')

            changes['deleted'].append({
                'change_obj': target_user_group.get_api_data(),
                'type': 'user_group', 'id': member_id,
                'name': member_name, 'new_perm': perm_name})

        return changes

    def get_perms_summary(self, user_group_id):
        permissions = {
            'repositories': {},
            'repositories_groups': {},
        }
        ugroup_repo_perms = UserGroupRepoToPerm.query()\
            .options(joinedload(UserGroupRepoToPerm.permission))\
            .options(joinedload(UserGroupRepoToPerm.repository))\
            .filter(UserGroupRepoToPerm.users_group_id == user_group_id)\
            .all()

        for gr in ugroup_repo_perms:
            permissions['repositories'][gr.repository.repo_name]  \
                = gr.permission.permission_name

        ugroup_group_perms = UserGroupRepoGroupToPerm.query()\
            .options(joinedload(UserGroupRepoGroupToPerm.permission))\
            .options(joinedload(UserGroupRepoGroupToPerm.group))\
            .filter(UserGroupRepoGroupToPerm.users_group_id == user_group_id)\
            .all()

        for gr in ugroup_group_perms:
            permissions['repositories_groups'][gr.group.group_name] \
                = gr.permission.permission_name
        return permissions

    def enforce_groups(self, user, groups, extern_type=None):
        user = self._get_user(user)
        current_groups = user.group_member

        # find the external created groups, i.e automatically created
        log.debug('Enforcing user group set `%s` on user %s', groups, user)
        # calculate from what groups user should be removed
        # external_groups that are not in groups
        for gr in [x.users_group for x in current_groups]:
            managed = gr.group_data.get('extern_type')
            if managed:
                if gr.users_group_name not in groups:
                    log.debug('Removing user %s from user group %s. '
                              'Group sync managed by: %s', user, gr, managed)
                    self.remove_user_from_group(gr, user)
            else:
                log.debug('Skipping removal from group %s since it is '
                          'not set to be automatically synchronized', gr)

        # now we calculate in which groups user should be == groups params
        owner = User.get_first_super_admin().username
        for gr in set(groups):
            existing_group = UserGroup.get_by_group_name(gr)
            if not existing_group:
                desc = 'Automatically created from plugin:%s' % extern_type
                # we use first admin account to set the owner of the group
                existing_group = UserGroupModel().create(
                    gr, desc, owner, group_data={'extern_type': extern_type})

            # we can only add users to groups which have set sync flag via
            # extern_type attribute.
            # This is either set and created via plugins, or manually
            managed = existing_group.group_data.get('extern_type')
            if managed:
                log.debug('Adding user %s to user group %s', user, gr)
                UserGroupModel().add_user_to_group(existing_group, user)
            else:
                log.debug('Skipping addition to group %s since it is '
                          'not set to be automatically synchronized', gr)

    def change_groups(self, user, groups):
        """
        This method changes user group assignment
        :param user:  User
        :param groups: array of UserGroupModel
        """
        user = self._get_user(user)
        log.debug('Changing user(%s) assignment to groups(%s)', user, groups)
        current_groups = user.group_member
        current_groups = [x.users_group for x in current_groups]

        # calculate from what groups user should be removed/add
        groups = set(groups)
        current_groups = set(current_groups)

        groups_to_remove = current_groups - groups
        groups_to_add = groups - current_groups

        removed_from_groups = []
        added_to_groups = []
        for gr in groups_to_remove:
            log.debug('Removing user %s from user group %s',
                      user.username, gr.users_group_name)
            removed_from_groups.append(gr.users_group_id)
            self.remove_user_from_group(gr.users_group_name, user.username)
        for gr in groups_to_add:
            log.debug('Adding user %s to user group %s',
                      user.username, gr.users_group_name)
            added_to_groups.append(gr.users_group_id)
            UserGroupModel().add_user_to_group(
                gr.users_group_name, user.username)

        return added_to_groups, removed_from_groups

    def _serialize_user_group(self, user_group):
        import rhodecode.lib.helpers as h
        return {
                'id': user_group.users_group_id,
                # TODO: marcink figure out a way to generate the url for the
                # icon
                'icon_link': '',
                'value_display': 'Group: %s (%d members)' % (
                    user_group.users_group_name, len(user_group.members),),
                'value': user_group.users_group_name,
                'description': user_group.user_group_description,
                'owner': user_group.user.username,

                'owner_icon': h.gravatar_url(user_group.user.email, 30),
                'value_display_owner': h.person(user_group.user.email),

                'value_type': 'user_group',
                'active': user_group.users_group_active,
            }

    def get_user_groups(self, name_contains=None, limit=20, only_active=True,
                        expand_groups=False):
        query = self.sa.query(UserGroup)
        if only_active:
            query = query.filter(UserGroup.users_group_active == true())

        if name_contains:
            ilike_expression = u'%{}%'.format(safe_unicode(name_contains))
            query = query.filter(
                UserGroup.users_group_name.ilike(ilike_expression))\
                .order_by(func.length(UserGroup.users_group_name))\
                .order_by(UserGroup.users_group_name)

            query = query.limit(limit)
        user_groups = query.all()
        perm_set = ['usergroup.read', 'usergroup.write', 'usergroup.admin']
        user_groups = UserGroupList(user_groups, perm_set=perm_set)

        # store same serialize method to extract data from User
        from rhodecode.model.user import UserModel
        serialize_user = UserModel()._serialize_user

        _groups = []
        for group in user_groups:
            entry = self._serialize_user_group(group)
            if expand_groups:
                expanded_members = []
                for member in group.members:
                    expanded_members.append(serialize_user(member.user))
                entry['members'] = expanded_members
            _groups.append(entry)
        return _groups

    @staticmethod
    def get_user_groups_as_dict(user_group):
        import rhodecode.lib.helpers as h

        data = {
            'users_group_id': user_group.users_group_id,
            'group_name': h.link_to_group(user_group.users_group_name),
            'group_description': user_group.user_group_description,
            'active': user_group.users_group_active,
            "owner": user_group.user.username,
            'owner_icon': h.gravatar_url(user_group.user.email, 30),
            "owner_data": {
                'owner': user_group.user.username,
                'owner_icon': h.gravatar_url(user_group.user.email, 30)}
            }
        return data
