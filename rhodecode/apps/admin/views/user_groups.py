# -*- coding: utf-8 -*-

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

import formencode
import formencode.htmlfill

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.renderers import render

from rhodecode import events
from rhodecode.apps._base import BaseAppView, DataGridAppView
from rhodecode.lib.auth import (
    LoginRequired, NotAnonymous, CSRFRequired, HasPermissionAnyDecorator)
from rhodecode.lib import helpers as h, audit_logger
from rhodecode.lib.utils2 import safe_unicode

from rhodecode.model.forms import UserGroupForm
from rhodecode.model.permission import PermissionModel
from rhodecode.model.scm import UserGroupList
from rhodecode.model.db import (
    or_, count, User, UserGroup, UserGroupMember, in_filter_generator)
from rhodecode.model.meta import Session
from rhodecode.model.user_group import UserGroupModel
from rhodecode.model.db import true

log = logging.getLogger(__name__)


class AdminUserGroupsView(BaseAppView, DataGridAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()

        PermissionModel().set_global_permission_choices(
            c, gettext_translator=self.request.translate)

        return c

    # permission check in data loading of
    # `user_groups_list_data` via UserGroupList
    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='user_groups', request_method='GET',
        renderer='rhodecode:templates/admin/user_groups/user_groups.mako')
    def user_groups_list(self):
        c = self.load_default_context()
        return self._get_template_context(c)

    # permission check inside
    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='user_groups_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def user_groups_list_data(self):
        self.load_default_context()
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

        _render = self.request.get_partial_renderer(
            'rhodecode:templates/data_table/_dt_elements.mako')

        def user_group_name(user_group_name):
            return _render("user_group_name", user_group_name)

        def user_group_actions(user_group_id, user_group_name):
            return _render("user_group_actions", user_group_id, user_group_name)

        def user_profile(username):
            return _render('user_profile', username)

        auth_user_group_list = UserGroupList(
            UserGroup.query().all(), perm_set=['usergroup.admin'])

        allowed_ids = [-1]
        for user_group in auth_user_group_list:
                allowed_ids.append(user_group.users_group_id)

        user_groups_data_total_count = UserGroup.query()\
            .filter(or_(
                # generate multiple IN to fix limitation problems
                *in_filter_generator(UserGroup.users_group_id, allowed_ids)
            ))\
            .count()

        user_groups_data_total_inactive_count = UserGroup.query()\
            .filter(or_(
                # generate multiple IN to fix limitation problems
                *in_filter_generator(UserGroup.users_group_id, allowed_ids)
            ))\
            .filter(UserGroup.users_group_active != true()).count()

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
            .filter(or_(
                # generate multiple IN to fix limitation problems
                *in_filter_generator(UserGroup.users_group_id, allowed_ids)
            )) \
            .outerjoin(UserGroupMember, UserGroupMember.users_group_id == UserGroup.users_group_id) \
            .join(User, User.user_id == UserGroup.user_id) \
            .group_by(UserGroup, User)

        base_q_inactive = base_q.filter(UserGroup.users_group_active != true())

        if search_q:
            like_expression = u'%{}%'.format(safe_unicode(search_q))
            base_q = base_q.filter(or_(
                UserGroup.users_group_name.ilike(like_expression),
            ))
            base_q_inactive = base_q.filter(UserGroup.users_group_active != true())

        user_groups_data_total_filtered_count = base_q.count()
        user_groups_data_total_filtered_inactive_count = base_q_inactive.count()

        sort_defined = False
        if order_by == 'members_total':
            sort_col = member_count
            sort_defined = True
        elif order_by == 'user_username':
            sort_col = User.username
        else:
            sort_col = getattr(UserGroup, order_by, None)

        if sort_defined or sort_col:
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
            row = {
                "users_group_name": user_group_name(user_gr.users_group_name),
                "name_raw": h.escape(user_gr.users_group_name),
                "description": h.escape(user_gr.user_group_description),
                "members": user_gr.member_count,
                # NOTE(marcink): because of advanced query we
                # need to load it like that
                "sync": UserGroup._load_sync(
                    UserGroup._load_group_data(user_gr.group_data)),
                "active": h.bool2icon(user_gr.users_group_active),
                "owner": user_profile(user_gr.User.username),
                "action": user_group_actions(
                    user_gr.users_group_id, user_gr.users_group_name)
            }
            user_groups_data.append(row)

        data = ({
            'draw': draw,
            'data': user_groups_data,
            'recordsTotal': user_groups_data_total_count,
            'recordsTotalInactive': user_groups_data_total_inactive_count,
            'recordsFiltered': user_groups_data_total_filtered_count,
            'recordsFilteredInactive': user_groups_data_total_filtered_inactive_count,
        })

        return data

    @LoginRequired()
    @HasPermissionAnyDecorator('hg.admin', 'hg.usergroup.create.true')
    @view_config(
        route_name='user_groups_new', request_method='GET',
        renderer='rhodecode:templates/admin/user_groups/user_group_add.mako')
    def user_groups_new(self):
        c = self.load_default_context()
        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAnyDecorator('hg.admin', 'hg.usergroup.create.true')
    @CSRFRequired()
    @view_config(
        route_name='user_groups_create', request_method='POST',
        renderer='rhodecode:templates/admin/user_groups/user_group_add.mako')
    def user_groups_create(self):
        _ = self.request.translate
        c = self.load_default_context()
        users_group_form = UserGroupForm(self.request.translate)()

        user_group_name = self.request.POST.get('users_group_name')
        try:
            form_result = users_group_form.to_python(dict(self.request.POST))
            user_group = UserGroupModel().create(
                name=form_result['users_group_name'],
                description=form_result['user_group_description'],
                owner=self._rhodecode_user.user_id,
                active=form_result['users_group_active'])
            Session().flush()
            creation_data = user_group.get_api_data()
            user_group_name = form_result['users_group_name']

            audit_logger.store_web(
                'user_group.create', action_data={'data': creation_data},
                user=self._rhodecode_user)

            user_group_link = h.link_to(
                h.escape(user_group_name),
                h.route_path(
                    'edit_user_group', user_group_id=user_group.users_group_id))
            h.flash(h.literal(_('Created user group %(user_group_link)s')
                              % {'user_group_link': user_group_link}),
                    category='success')
            Session().commit()
            user_group_id = user_group.users_group_id
        except formencode.Invalid as errors:

            data = render(
                'rhodecode:templates/admin/user_groups/user_group_add.mako',
                self._get_template_context(c), self.request)
            html = formencode.htmlfill.render(
                data,
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False
            )
            return Response(html)

        except Exception:
            log.exception("Exception creating user group")
            h.flash(_('Error occurred during creation of user group %s') \
                    % user_group_name, category='error')
            raise HTTPFound(h.route_path('user_groups_new'))

        affected_user_ids = [self._rhodecode_user.user_id]
        PermissionModel().trigger_permission_flush(affected_user_ids)

        raise HTTPFound(
            h.route_path('edit_user_group', user_group_id=user_group_id))
