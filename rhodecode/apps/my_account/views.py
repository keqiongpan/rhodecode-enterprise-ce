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

from rhodecode.apps._base import BaseAppView
from rhodecode import forms
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, NotAnonymous, CSRFRequired
from rhodecode.lib.channelstream import channelstream_request, \
    ChannelstreamException
from rhodecode.lib.utils2 import safe_int, md5
from rhodecode.model.auth_token import AuthTokenModel
from rhodecode.model.meta import Session
from rhodecode.model.user import UserModel
from rhodecode.model.validation_schema.schemas import user_schema

log = logging.getLogger(__name__)


class MyAccountView(BaseAppView):
    ALLOW_SCOPED_TOKENS = False
    """
    This view has alternative version inside EE, if modified please take a look
    in there as well.
    """

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.user = c.auth_user.get_instance()
        c.allow_scoped_tokens = self.ALLOW_SCOPED_TOKENS
        self._register_global_c(c)
        return c

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_profile', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_profile(self):
        c = self.load_default_context()
        c.active = 'profile'
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_password', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_password(self):
        c = self.load_default_context()
        c.active = 'password'
        c.extern_type = c.user.extern_type

        schema = user_schema.ChangePasswordSchema().bind(
            username=c.user.username)

        form = forms.Form(
            schema, buttons=(forms.buttons.save, forms.buttons.reset))

        c.form = form
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_password', request_method='POST',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_password_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'password'
        c.extern_type = c.user.extern_type

        schema = user_schema.ChangePasswordSchema().bind(
            username=c.user.username)

        form = forms.Form(
            schema, buttons=(forms.buttons.save, forms.buttons.reset))

        if c.extern_type != 'rhodecode':
            raise HTTPFound(self.request.route_path('my_account_password'))

        controls = self.request.POST.items()
        try:
            valid_data = form.validate(controls)
            UserModel().update_user(c.user.user_id, **valid_data)
            c.user.update_userdata(force_password_change=False)
            Session().commit()
        except forms.ValidationFailure as e:
            c.form = e
            return self._get_template_context(c)

        except Exception:
            log.exception("Exception updating password")
            h.flash(_('Error occurred during update of user password'),
                    category='error')
        else:
            instance = c.auth_user.get_instance()
            self.session.setdefault('rhodecode_user', {}).update(
                {'password': md5(instance.password)})
            self.session.save()
            h.flash(_("Successfully updated password"), category='success')

        raise HTTPFound(self.request.route_path('my_account_password'))

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='my_account_auth_tokens', request_method='GET',
        renderer='rhodecode:templates/admin/my_account/my_account.mako')
    def my_account_auth_tokens(self):
        _ = self.request.translate

        c = self.load_default_context()
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

        token = AuthTokenModel().create(
            c.user.user_id, description, lifetime, role)
        self.maybe_attach_token_scope(token)
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

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='my_account_notifications_test_channelstream',
        request_method='POST', renderer='json_ext')
    def my_account_notifications_test_channelstream(self):
        message = 'Test message sent via Channelstream by user: {}, on {}'.format(
            self._rhodecode_user.username, datetime.datetime.now())
        payload = {
            # 'channel': 'broadcast',
            'type': 'message',
            'timestamp': datetime.datetime.utcnow(),
            'user': 'system',
            'pm_users': [self._rhodecode_user.username],
            'message': {
                'message': message,
                'level': 'info',
                'topic': '/notifications'
            }
        }

        registry = self.request.registry
        rhodecode_plugins = getattr(registry, 'rhodecode_plugins', {})
        channelstream_config = rhodecode_plugins.get('channelstream', {})

        try:
            channelstream_request(channelstream_config, [payload], '/message')
        except ChannelstreamException as e:
            log.exception('Failed to send channelstream data')
            return {"response": 'ERROR: {}'.format(e.__class__.__name__)}
        return {"response": 'Channelstream data sent. '
                            'You should see a new live message now.'}
