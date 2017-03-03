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

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from rhodecode.apps._base import BaseAppView
from rhodecode.lib.auth import LoginRequired, NotAnonymous, CSRFRequired
from rhodecode.lib.utils2 import safe_int
from rhodecode.lib import helpers as h
from rhodecode.model.auth_token import AuthTokenModel
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


class MyAccountView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()

        c.auth_user = self.request.user
        c.user = c.auth_user.get_instance()

        self._register_global_c(c)
        return c

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_auth_tokens', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_auth_tokens(self):
        _ = self.request.translate

        c = self.load_default_context()
        c.active = 'auth_tokens'

        show_expired = True

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
            c.user.user_id, show_expired=show_expired)
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_auth_tokens_add', request_method='POST')
    def my_account_auth_tokens_add(self):
        _ = self.request.translate
        c = self.load_default_context()

        lifetime = safe_int(self.request.POST.get('lifetime'), -1)
        description = self.request.POST.get('description')
        role = self.request.POST.get('role')

        AuthTokenModel().create(c.user.user_id, description, lifetime, role)
        Session().commit()
        h.flash(_("Auth token successfully created"), category='success')

        return HTTPFound(h.route_path('my_account_auth_tokens'))

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_auth_tokens_delete', request_method='POST')
    def my_account_auth_tokens_delete(self):
        _ = self.request.translate
        c = self.load_default_context()

        del_auth_token = self.request.POST.get('del_auth_token')

        if del_auth_token:
            AuthTokenModel().delete(del_auth_token, c.user.user_id)
            Session().commit()
            h.flash(_("Auth token successfully deleted"), category='success')

        return HTTPFound(h.route_path('my_account_auth_tokens'))
