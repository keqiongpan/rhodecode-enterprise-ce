# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 RhodeCode GmbH
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
import datetime

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from rhodecode.model.scm import UserGroupList

from rhodecode.apps._base import BaseAppView, DataGridAppView
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired, NotAnonymous,
    HasUserGroupPermissionAnyDecorator)
from rhodecode.lib import helpers as h
from rhodecode.lib.utils import PartialRenderer
from rhodecode.lib.utils2 import safe_int, safe_unicode
from rhodecode.model.user_group import UserGroupModel
from rhodecode.model.db import (
    joinedload, or_, count, User, UserGroup, UserGroupMember,
    UserGroupRepoToPerm, UserGroupRepoGroupToPerm)
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


class AdminUserGroupsView(BaseAppView, DataGridAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        self._register_global_c(c)
        return c

    # permission check in data loading of
    # `user_groups_list_data` via UserGroupList
    @NotAnonymous()
    @view_config(
        route_name='user_groups', request_method='GET',
        renderer='rhodecode:templates/admin/user_groups/user_groups.mako')
    def user_groups_list(self):
        c = self.load_default_context()
        return self._get_template_context(c)

    # permission check inside
    @NotAnonymous()
    @view_config(
        route_name='user_groups_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def user_groups_list_data(self):
        column_map = {
            'active': 'users_group_active',
            'description': 'user_group_description',
            'members': 'members_total',
            'owner': 'user_username',
            'sync': 'group_data'
        }
        draw, start, limit = self._extract_chunk(self.request)
        search_q, order_by, order_dir = self._extract_ordering(
            self.request, column_map=column_map)

        _render = PartialRenderer('data_table/_dt_elements.mako')

        def user_group_name(user_group_id, user_group_name):
            return _render("user_group_name", user_group_id, user_group_name)

        def user_group_actions(user_group_id, user_group_name):
            return _render("user_group_actions", user_group_id, user_group_name)

        def user_profile(username):
            return _render('user_profile', username)

        auth_user_group_list = UserGroupList(
            UserGroup.query().all(), perm_set=['usergroup.admin'])

        allowed_ids = []
        for user_group in auth_user_group_list:
                allowed_ids.append(user_group.users_group_id)

        user_groups_data_total_count = UserGroup.query()\
            .filter(UserGroup.users_group_id.in_(allowed_ids))\
            .count()

        member_count = count(UserGroupMember.user_id)
        base_q = Session.query(
            UserGroup.users_group_name,
            UserGroup.user_group_description,
            UserGroup.users_group_active,
            UserGroup.users_group_id,
            UserGroup.group_data,
            User,
            member_count.label('member_count')
        ) \
        .filter(UserGroup.users_group_id.in_(allowed_ids)) \
        .outerjoin(UserGroupMember) \
        .join(User, User.user_id == UserGroup.user_id) \
        .group_by(UserGroup, User)

        if search_q:
            like_expression = u'%{}%'.format(safe_unicode(search_q))
            base_q = base_q.filter(or_(
                UserGroup.users_group_name.ilike(like_expression),
            ))

        user_groups_data_total_filtered_count = base_q.count()

        if order_by == 'members_total':
            sort_col = member_count
        elif order_by == 'user_username':
            sort_col = User.username
        else:
            sort_col = getattr(UserGroup, order_by, None)

        if isinstance(sort_col, count) or sort_col:
            if order_dir == 'asc':
                sort_col = sort_col.asc()
            else:
                sort_col = sort_col.desc()

        base_q = base_q.order_by(sort_col)
        base_q = base_q.offset(start).limit(limit)

        # authenticated access to user groups
        auth_user_group_list = base_q.all()

        user_groups_data = []
        for user_gr in auth_user_group_list:
            user_groups_data.append({
                "users_group_name": user_group_name(
                    user_gr.users_group_id, h.escape(user_gr.users_group_name)),
                "name_raw": h.escape(user_gr.users_group_name),
                "description": h.escape(user_gr.user_group_description),
                "members": user_gr.member_count,
                # NOTE(marcink): because of advanced query we
                # need to load it like that
                "sync": UserGroup._load_group_data(
                    user_gr.group_data).get('extern_type'),
                "active": h.bool2icon(user_gr.users_group_active),
                "owner": user_profile(user_gr.User.username),
                "action": user_group_actions(
                    user_gr.users_group_id, user_gr.users_group_name)
            })

        data = ({
            'draw': draw,
            'data': user_groups_data,
            'recordsTotal': user_groups_data_total_count,
            'recordsFiltered': user_groups_data_total_filtered_count,
        })

        return data

    @LoginRequired()
    @HasUserGroupPermissionAnyDecorator('usergroup.admin')
    @view_config(
        route_name='user_group_members_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def user_group_members(self):
        """
        Return members of given user group
        """
        user_group_id = self.request.matchdict['user_group_id']
        user_group = UserGroup.get_or_404(user_group_id)
        group_members_obj = sorted((x.user for x in user_group.members),
                                   key=lambda u: u.username.lower())

        group_members = [
            {
                'id': user.user_id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'icon_link': h.gravatar_url(user.email, 30),
                'value_display': h.person(user.email),
                'value': user.username,
                'value_type': 'user',
                'active': user.active,
            }
            for user in group_members_obj
        ]

        return {
            'members': group_members
        }

    def _get_perms_summary(self, user_group_id):
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

    @LoginRequired()
    @HasUserGroupPermissionAnyDecorator('usergroup.admin')
    @view_config(
        route_name='edit_user_group_perms_summary', request_method='GET',
        renderer='rhodecode:templates/admin/user_groups/user_group_edit.mako')
    def user_group_perms_summary(self):
        c = self.load_default_context()

        user_group_id = self.request.matchdict.get('user_group_id')
        c.user_group = UserGroup.get_or_404(user_group_id)

        c.active = 'perms_summary'

        c.permissions = self._get_perms_summary(c.user_group.users_group_id)
        return self._get_template_context(c)

    @LoginRequired()
    @HasUserGroupPermissionAnyDecorator('usergroup.admin')
    @view_config(
        route_name='edit_user_group_perms_summary_json', request_method='GET',
        renderer='json_ext')
    def user_group_perms_summary(self):
        self.load_default_context()

        user_group_id = self.request.matchdict.get('user_group_id')
        user_group = UserGroup.get_or_404(user_group_id)

        return self._get_perms_summary(user_group.users_group_id)
