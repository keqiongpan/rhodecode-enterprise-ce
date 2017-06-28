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
import formencode

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from sqlalchemy.sql.functions import coalesce

from rhodecode.apps._base import BaseAppView, DataGridAppView

from rhodecode.lib import audit_logger
from rhodecode.lib.ext_json import json
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired)
from rhodecode.lib import helpers as h
from rhodecode.lib.utils import PartialRenderer
from rhodecode.lib.utils2 import safe_int, safe_unicode
from rhodecode.model.auth_token import AuthTokenModel
from rhodecode.model.user import UserModel
from rhodecode.model.user_group import UserGroupModel
from rhodecode.model.db import User, or_, UserIpMap, UserEmailMap, UserApiKeys
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


class AdminUsersView(BaseAppView, DataGridAppView):
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
        route_name='users_data', request_method='GET',
        renderer='json_ext', xhr=True)
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
                "first_name": user.first_name,
                "last_name": user.last_name,
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

        user_data = c.user.get_api_data()
        lifetime = safe_int(self.request.POST.get('lifetime'), -1)
        description = self.request.POST.get('description')
        role = self.request.POST.get('role')

        token = AuthTokenModel().create(
            c.user.user_id, description, lifetime, role)
        token_data = token.get_api_data()

        self.maybe_attach_token_scope(token)
        audit_logger.store_web(
            'user.edit.token.add', action_data={
                'data': {'token': token_data, 'user': user_data}},
            user=self._rhodecode_user, )
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
        user_data = c.user.get_api_data()

        del_auth_token = self.request.POST.get('del_auth_token')

        if del_auth_token:
            token = UserApiKeys.get_or_404(del_auth_token, pyramid_exc=True)
            token_data = token.get_api_data()

            AuthTokenModel().delete(del_auth_token, c.user.user_id)
            audit_logger.store_web(
                'user.edit.token.delete', action_data={
                    'data': {'token': token_data, 'user': user_data}},
                user=self._rhodecode_user,)
            Session().commit()
            h.flash(_("Auth token successfully deleted"), category='success')

        return HTTPFound(h.route_path('edit_user_auth_tokens', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='edit_user_emails', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')
    def emails(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.request.matchdict.get('user_id')
        c.user = User.get_or_404(user_id, pyramid_exc=True)
        self._redirect_for_default_user(c.user.username)

        c.active = 'emails'
        c.user_email_map = UserEmailMap.query() \
            .filter(UserEmailMap.user == c.user).all()

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_user_emails_add', request_method='POST')
    def emails_add(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.request.matchdict.get('user_id')
        c.user = User.get_or_404(user_id, pyramid_exc=True)
        self._redirect_for_default_user(c.user.username)

        email = self.request.POST.get('new_email')
        user_data = c.user.get_api_data()
        try:
            UserModel().add_extra_email(c.user.user_id, email)
            audit_logger.store_web(
                'user.edit.email.add', action_data={'email': email, 'user': user_data},
                user=self._rhodecode_user)
            Session().commit()
            h.flash(_("Added new email address `%s` for user account") % email,
                    category='success')
        except formencode.Invalid as error:
            h.flash(h.escape(error.error_dict['email']), category='error')
        except Exception:
            log.exception("Exception during email saving")
            h.flash(_('An error occurred during email saving'),
                    category='error')
        raise HTTPFound(h.route_path('edit_user_emails', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_user_emails_delete', request_method='POST')
    def emails_delete(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.request.matchdict.get('user_id')
        c.user = User.get_or_404(user_id, pyramid_exc=True)
        self._redirect_for_default_user(c.user.username)

        email_id = self.request.POST.get('del_email_id')
        user_model = UserModel()

        email = UserEmailMap.query().get(email_id).email
        user_data = c.user.get_api_data()
        user_model.delete_extra_email(c.user.user_id, email_id)
        audit_logger.store_web(
            'user.edit.email.delete', action_data={'email': email, 'user': user_data},
            user=self._rhodecode_user)
        Session().commit()
        h.flash(_("Removed email address from user account"),
                category='success')
        raise HTTPFound(h.route_path('edit_user_emails', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='edit_user_ips', request_method='GET',
        renderer='rhodecode:templates/admin/users/user_edit.mako')
    def ips(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.request.matchdict.get('user_id')
        c.user = User.get_or_404(user_id, pyramid_exc=True)
        self._redirect_for_default_user(c.user.username)

        c.active = 'ips'
        c.user_ip_map = UserIpMap.query() \
            .filter(UserIpMap.user == c.user).all()

        c.inherit_default_ips = c.user.inherit_default_permissions
        c.default_user_ip_map = UserIpMap.query() \
            .filter(UserIpMap.user == User.get_default_user()).all()

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_user_ips_add', request_method='POST')
    def ips_add(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.request.matchdict.get('user_id')
        c.user = User.get_or_404(user_id, pyramid_exc=True)
        # NOTE(marcink): this view is allowed for default users, as we can
        # edit their IP white list

        user_model = UserModel()
        desc = self.request.POST.get('description')
        try:
            ip_list = user_model.parse_ip_range(
                self.request.POST.get('new_ip'))
        except Exception as e:
            ip_list = []
            log.exception("Exception during ip saving")
            h.flash(_('An error occurred during ip saving:%s' % (e,)),
                    category='error')
        added = []
        user_data = c.user.get_api_data()
        for ip in ip_list:
            try:
                user_model.add_extra_ip(c.user.user_id, ip, desc)
                audit_logger.store_web(
                    'user.edit.ip.add', action_data={'ip': ip, 'user': user_data},
                    user=self._rhodecode_user)
                Session().commit()
                added.append(ip)
            except formencode.Invalid as error:
                msg = error.error_dict['ip']
                h.flash(msg, category='error')
            except Exception:
                log.exception("Exception during ip saving")
                h.flash(_('An error occurred during ip saving'),
                        category='error')
        if added:
            h.flash(
                _("Added ips %s to user whitelist") % (', '.join(ip_list), ),
                category='success')
        if 'default_user' in self.request.POST:
            # case for editing global IP list we do it for 'DEFAULT' user
            raise HTTPFound(h.route_path('admin_permissions_ips'))
        raise HTTPFound(h.route_path('edit_user_ips', user_id=user_id))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_user_ips_delete', request_method='POST')
    def ips_delete(self):
        _ = self.request.translate
        c = self.load_default_context()

        user_id = self.request.matchdict.get('user_id')
        c.user = User.get_or_404(user_id, pyramid_exc=True)
        # NOTE(marcink): this view is allowed for default users, as we can
        # edit their IP white list

        ip_id = self.request.POST.get('del_ip_id')
        user_model = UserModel()
        user_data = c.user.get_api_data()
        ip = UserIpMap.query().get(ip_id).ip_addr
        user_model.delete_extra_ip(c.user.user_id, ip_id)
        audit_logger.store_web(
            'user.edit.ip.delete', action_data={'ip': ip, 'user': user_data},
            user=self._rhodecode_user)
        Session().commit()
        h.flash(_("Removed ip address from user whitelist"), category='success')

        if 'default_user' in self.request.POST:
            # case for editing global IP list we do it for 'DEFAULT' user
            raise HTTPFound(h.route_path('admin_permissions_ips'))
        raise HTTPFound(h.route_path('edit_user_ips', user_id=user_id))

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
        groups = [UserGroupModel.get_user_groups_as_dict(group.users_group)
                  for group in c.user.group_member]
        c.groups = json.dumps(groups)
        c.active = 'groups'

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
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
        user_log = UserModel().get_user_log(c.user, filter_term)

        def url_generator(**kw):
            if filter_term:
                kw['filter'] = filter_term
            return self.request.current_route_path(_query=kw)

        c.audit_logs = h.Page(
            user_log, page=p, items_per_page=10, url=url_generator)
        c.filter_term = filter_term
        return self._get_template_context(c)

