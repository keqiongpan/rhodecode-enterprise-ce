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
from sqlalchemy.sql.functions import coalesce

from rhodecode.lib.helpers import Page
from rhodecode_tools.lib.ext_json import json

from rhodecode.apps._base import BaseAppView
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired)
from rhodecode.lib import helpers as h
from rhodecode.lib.utils import PartialRenderer
from rhodecode.lib.utils2 import safe_int, safe_unicode
from rhodecode.model.auth_token import AuthTokenModel
from rhodecode.model.user import UserModel
from rhodecode.model.user_group import UserGroupModel
from rhodecode.model.db import User, or_
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


class AdminUsersView(BaseAppView):
    ALLOW_SCOPED_TOKENS = False
    """
    This view has alternative version inside EE, if modified please take a look
    in there as well.
    """

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.allow_scoped_tokens = self.ALLOW_SCOPED_TOKENS
        self._register_global_c(c)
        return c

    def _redirect_for_default_user(self, username):
        _ = self.request.translate
        if username == User.DEFAULT_USER:
            h.flash(_("You can't edit this user"), category='warning')
            # TODO(marcink): redirect to 'users' admin panel once this
            # is a pyramid view
            raise HTTPFound('/')

    def _extract_ordering(self, request):
        column_index = safe_int(request.GET.get('order[0][column]'))
        order_dir = request.GET.get(
            'order[0][dir]', 'desc')
        order_by = request.GET.get(
            'columns[%s][data][sort]' % column_index, 'name_raw')

        # translate datatable to DB columns
        order_by = {
            'first_name': 'name',
            'last_name': 'lastname',
        }.get(order_by) or order_by

        search_q = request.GET.get('search[value]')
        return search_q, order_by, order_dir

    def _extract_chunk(self, request):
        start = safe_int(request.GET.get('start'), 0)
        length = safe_int(request.GET.get('length'), 25)
        draw = safe_int(request.GET.get('draw'))
        return draw, start, length

    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='users', request_method='GET',
        renderer='rhodecode:templates/admin/users/users.mako')
    def users_list(self):
        c = self.load_default_context()
        return self._get_template_context(c)

    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        # renderer defined below
        route_name='users_data', request_method='GET', renderer='json',
        xhr=True)
    def users_list_data(self):
        draw, start, limit = self._extract_chunk(self.request)
        search_q, order_by, order_dir = self._extract_ordering(self.request)

        _render = PartialRenderer('data_table/_dt_elements.mako')

        def user_actions(user_id, username):
            return _render("user_actions", user_id, username)

        users_data_total_count = User.query()\
            .filter(User.username != User.DEFAULT_USER) \
            .count()

        # json generate
        base_q = User.query().filter(User.username != User.DEFAULT_USER)

        if search_q:
            like_expression = u'%{}%'.format(safe_unicode(search_q))
            base_q = base_q.filter(or_(
                User.username.ilike(like_expression),
                User._email.ilike(like_expression),
                User.name.ilike(like_expression),
                User.lastname.ilike(like_expression),
            ))

        users_data_total_filtered_count = base_q.count()

        sort_col = getattr(User, order_by, None)
        if sort_col:
            if order_dir == 'asc':
                # handle null values properly to order by NULL last
                if order_by in ['last_activity']:
                    sort_col = coalesce(sort_col, datetime.date.max)
                sort_col = sort_col.asc()
            else:
                # handle null values properly to order by NULL last
                if order_by in ['last_activity']:
                    sort_col = coalesce(sort_col, datetime.date.min)
                sort_col = sort_col.desc()

        base_q = base_q.order_by(sort_col)
        base_q = base_q.offset(start).limit(limit)

        users_list = base_q.all()

        users_data = []
        for user in users_list:
            users_data.append({
                "username": h.gravatar_with_user(user.username),
                "email": user.email,
                "first_name": h.escape(user.name),
                "last_name": h.escape(user.lastname),
                "last_login": h.format_date(user.last_login),
                "last_activity": h.format_date(user.last_activity),
                "active": h.bool2icon(user.active),
                "active_raw": user.active,
                "admin": h.bool2icon(user.admin),
                "extern_type": user.extern_type,
                "extern_name": user.extern_name,
                "action": user_actions(user.user_id, user.username),
            })

        data = ({
            'draw': draw,
            'data': users_data,
            'recordsTotal': users_data_total_count,
            'recordsFiltered': users_data_total_filtered_count,
        })

        return data

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='edit_user_auth_tokens', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')
    def auth_tokens(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.request.matchdict.get('user_id')
        c.user = User.get_or_404(user_id, pyramid_exc=True)
        self._redirect_for_default_user(c.user.username)

        c.active = 'auth_tokens'

        c.lifetime_values = [
            (str(-1), _('forever')),
            (str(5), _('5 minutes')),
            (str(60), _('1 hour')),
            (str(60 * 24), _('1 day')),
            (str(60 * 24 * 30), _('1 month')),
        ]
        c.lifetime_options = [(c.lifetime_values, _("Lifetime"))]
        c.role_values = [
            (x, AuthTokenModel.cls._get_role_name(x))
            for x in AuthTokenModel.cls.ROLES]
        c.role_options = [(c.role_values, _("Role"))]
        c.user_auth_tokens = AuthTokenModel().get_auth_tokens(
            c.user.user_id, show_expired=True)
        return self._get_template_context(c)

    def maybe_attach_token_scope(self, token):
        # implemented in EE edition
        pass

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_user_auth_tokens_add', request_method='POST')
    def auth_tokens_add(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.request.matchdict.get('user_id')
        c.user = User.get_or_404(user_id, pyramid_exc=True)
        self._redirect_for_default_user(c.user.username)

        lifetime = safe_int(self.request.POST.get('lifetime'), -1)
        description = self.request.POST.get('description')
        role = self.request.POST.get('role')

        token = AuthTokenModel().create(
            c.user.user_id, description, lifetime, role)
        self.maybe_attach_token_scope(token)
        Session().commit()

        h.flash(_("Auth token successfully created"), category='success')
        return HTTPFound(h.route_path('edit_user_auth_tokens', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_user_auth_tokens_delete', request_method='POST')
    def auth_tokens_delete(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.request.matchdict.get('user_id')
        c.user = User.get_or_404(user_id, pyramid_exc=True)
        self._redirect_for_default_user(c.user.username)

        del_auth_token = self.request.POST.get('del_auth_token')

        if del_auth_token:
            AuthTokenModel().delete(del_auth_token, c.user.user_id)
            Session().commit()
            h.flash(_("Auth token successfully deleted"), category='success')

        return HTTPFound(h.route_path('edit_user_auth_tokens', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='edit_user_groups_management', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')
    def groups_management(self):
        c = self.load_default_context()

        user_id = self.request.matchdict.get('user_id')
        c.user = User.get_or_404(user_id, pyramid_exc=True)
        c.data = c.user.group_member
        self._redirect_for_default_user(c.user.username)
        groups = [UserGroupModel.get_user_groups_as_dict(group.users_group) for group in c.user.group_member]
        c.groups = json.dumps(groups)
        c.active = 'groups'

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='edit_user_groups_management_updates', request_method='POST')
    def groups_management_updates(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.request.matchdict.get('user_id')
        c.user = User.get_or_404(user_id, pyramid_exc=True)
        self._redirect_for_default_user(c.user.username)

        users_groups = set(self.request.POST.getall('users_group_id'))
        users_groups_model = []

        for ugid in users_groups:
            users_groups_model.append(UserGroupModel().get_group(safe_int(ugid)))
        user_group_model = UserGroupModel()
        user_group_model.change_groups(c.user, users_groups_model)

        Session().commit()
        c.active = 'user_groups_management'
        h.flash(_("Groups successfully changed"), category='success')

        return HTTPFound(h.route_path(
            'edit_user_groups_management', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='edit_user_audit_logs', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')
    def user_audit_logs(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.request.matchdict.get('user_id')
        c.user = User.get_or_404(user_id, pyramid_exc=True)
        self._redirect_for_default_user(c.user.username)
        c.active = 'audit'

        p = safe_int(self.request.GET.get('page', 1), 1)

        filter_term = self.request.GET.get('filter')
        c.user_log = UserModel().get_user_log(c.user, filter_term)

        def url_generator(**kw):
            if filter_term:
                kw['filter'] = filter_term
            return self.request.current_route_path(_query=kw)

        c.user_log = Page(c.user_log, page=p, items_per_page=10,
                          url=url_generator)
        c.filter_term = filter_term
        return self._get_template_context(c)

