# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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

import time
import collections
import datetime
import formencode
import formencode.htmlfill
import logging
import urlparse
import requests

from pyramid.httpexceptions import HTTPFound


from rhodecode.apps._base import BaseAppView
from rhodecode.authentication.base import authenticate, HTTP_TYPE
from rhodecode.authentication.plugins import auth_rhodecode
from rhodecode.events import UserRegistered, trigger
from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import (
    AuthUser, HasPermissionAnyDecorator, CSRFRequired)
from rhodecode.lib.base import get_ip_addr
from rhodecode.lib.exceptions import UserCreationError
from rhodecode.lib.utils2 import safe_str
from rhodecode.model.db import User, UserApiKeys
from rhodecode.model.forms import LoginForm, RegisterForm, PasswordResetForm
from rhodecode.model.meta import Session
from rhodecode.model.auth_token import AuthTokenModel
from rhodecode.model.settings import SettingsModel
from rhodecode.model.user import UserModel
from rhodecode.translation import _


log = logging.getLogger(__name__)

CaptchaData = collections.namedtuple(
    'CaptchaData', 'active, private_key, public_key')


def store_user_in_session(session, username, remember=False):
    user = User.get_by_username(username, case_insensitive=True)
    auth_user = AuthUser(user.user_id)
    auth_user.set_authenticated()
    cs = auth_user.get_cookie_store()
    session['rhodecode_user'] = cs
    user.update_lastlogin()
    Session().commit()

    # If they want to be remembered, update the cookie
    if remember:
        _year = (datetime.datetime.now() +
                 datetime.timedelta(seconds=60 * 60 * 24 * 365))
        session._set_cookie_expires(_year)

    session.save()

    safe_cs = cs.copy()
    safe_cs['password'] = '****'
    log.info('user %s is now authenticated and stored in '
             'session, session attrs %s', username, safe_cs)

    # dumps session attrs back to cookie
    session._update_cookie_out()
    # we set new cookie
    headers = None
    if session.request['set_cookie']:
        # send set-cookie headers back to response to update cookie
        headers = [('Set-Cookie', session.request['cookie_out'])]
    return headers


def get_came_from(request):
    came_from = safe_str(request.GET.get('came_from', ''))
    parsed = urlparse.urlparse(came_from)
    allowed_schemes = ['http', 'https']
    default_came_from = h.route_path('home')
    if parsed.scheme and parsed.scheme not in allowed_schemes:
        log.error('Suspicious URL scheme detected %s for url %s',
                  parsed.scheme, parsed)
        came_from = default_came_from
    elif parsed.netloc and request.host != parsed.netloc:
        log.error('Suspicious NETLOC detected %s for url %s server url '
                  'is: %s', parsed.netloc, parsed, request.host)
        came_from = default_came_from
    elif any(bad_str in parsed.path for bad_str in ('\r', '\n')):
        log.error('Header injection detected `%s` for url %s server url ',
                  parsed.path, parsed)
        came_from = default_came_from

    return came_from or default_came_from


class LoginView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.came_from = get_came_from(self.request)
        return c

    def _get_captcha_data(self):
        settings = SettingsModel().get_all_settings()
        private_key = settings.get('rhodecode_captcha_private_key')
        public_key = settings.get('rhodecode_captcha_public_key')
        active = bool(private_key)
        return CaptchaData(
            active=active, private_key=private_key, public_key=public_key)

    def validate_captcha(self, private_key):

        captcha_rs = self.request.POST.get('g-recaptcha-response')
        url = "https://www.google.com/recaptcha/api/siteverify"
        params = {
            'secret': private_key,
            'response': captcha_rs,
            'remoteip': get_ip_addr(self.request.environ)
        }
        verify_rs = requests.get(url, params=params, verify=True, timeout=60)
        verify_rs = verify_rs.json()
        captcha_status = verify_rs.get('success', False)
        captcha_errors = verify_rs.get('error-codes', [])
        if not isinstance(captcha_errors, list):
            captcha_errors = [captcha_errors]
        captcha_errors = ', '.join(captcha_errors)
        captcha_message = ''
        if captcha_status is False:
            captcha_message = "Bad captcha. Errors: {}".format(
                captcha_errors)

        return captcha_status, captcha_message

    def login(self):
        c = self.load_default_context()
        auth_user = self._rhodecode_user

        # redirect if already logged in
        if (auth_user.is_authenticated and
                not auth_user.is_default and auth_user.ip_allowed):
            raise HTTPFound(c.came_from)

        # check if we use headers plugin, and try to login using it.
        try:
            log.debug('Running PRE-AUTH for headers based authentication')
            auth_info = authenticate(
                '', '', self.request.environ, HTTP_TYPE, skip_missing=True)
            if auth_info:
                headers = store_user_in_session(
                    self.session, auth_info.get('username'))
                raise HTTPFound(c.came_from, headers=headers)
        except UserCreationError as e:
            log.error(e)
            h.flash(e, category='error')

        return self._get_template_context(c)

    def login_post(self):
        c = self.load_default_context()

        login_form = LoginForm(self.request.translate)()

        try:
            self.session.invalidate()
            form_result = login_form.to_python(self.request.POST)
            # form checks for username/password, now we're authenticated
            headers = store_user_in_session(
                self.session,
                username=form_result['username'],
                remember=form_result['remember'])
            log.debug('Redirecting to "%s" after login.', c.came_from)

            audit_user = audit_logger.UserWrap(
                username=self.request.POST.get('username'),
                ip_addr=self.request.remote_addr)
            action_data = {'user_agent': self.request.user_agent}
            audit_logger.store_web(
                'user.login.success', action_data=action_data,
                user=audit_user, commit=True)

            raise HTTPFound(c.came_from, headers=headers)
        except formencode.Invalid as errors:
            defaults = errors.value
            # remove password from filling in form again
            defaults.pop('password', None)
            render_ctx = {
                'errors': errors.error_dict,
                'defaults': defaults,
            }

            audit_user = audit_logger.UserWrap(
                username=self.request.POST.get('username'),
                ip_addr=self.request.remote_addr)
            action_data = {'user_agent': self.request.user_agent}
            audit_logger.store_web(
                'user.login.failure', action_data=action_data,
                user=audit_user, commit=True)
            return self._get_template_context(c, **render_ctx)

        except UserCreationError as e:
            # headers auth or other auth functions that create users on
            # the fly can throw this exception signaling that there's issue
            # with user creation, explanation should be provided in
            # Exception itself
            h.flash(e, category='error')
            return self._get_template_context(c)

    @CSRFRequired()
    def logout(self):
        auth_user = self._rhodecode_user
        log.info('Deleting session for user: `%s`', auth_user)

        action_data = {'user_agent': self.request.user_agent}
        audit_logger.store_web(
            'user.logout', action_data=action_data,
            user=auth_user, commit=True)
        self.session.delete()
        return HTTPFound(h.route_path('home'))

    @HasPermissionAnyDecorator(
        'hg.admin', 'hg.register.auto_activate', 'hg.register.manual_activate')
    def register(self, defaults=None, errors=None):
        c = self.load_default_context()
        defaults = defaults or {}
        errors = errors or {}

        settings = SettingsModel().get_all_settings()
        register_message = settings.get('rhodecode_register_message') or ''
        captcha = self._get_captcha_data()
        auto_active = 'hg.register.auto_activate' in User.get_default_user()\
            .AuthUser().permissions['global']

        render_ctx = self._get_template_context(c)
        render_ctx.update({
            'defaults': defaults,
            'errors': errors,
            'auto_active': auto_active,
            'captcha_active': captcha.active,
            'captcha_public_key': captcha.public_key,
            'register_message': register_message,
        })
        return render_ctx

    @HasPermissionAnyDecorator(
        'hg.admin', 'hg.register.auto_activate', 'hg.register.manual_activate')
    def register_post(self):
        from rhodecode.authentication.plugins import auth_rhodecode

        self.load_default_context()
        captcha = self._get_captcha_data()
        auto_active = 'hg.register.auto_activate' in User.get_default_user()\
            .AuthUser().permissions['global']

        extern_name = auth_rhodecode.RhodeCodeAuthPlugin.uid
        extern_type = auth_rhodecode.RhodeCodeAuthPlugin.uid

        register_form = RegisterForm(self.request.translate)()
        try:

            form_result = register_form.to_python(self.request.POST)
            form_result['active'] = auto_active
            external_identity = self.request.POST.get('external_identity')

            if external_identity:
                extern_name = external_identity
                extern_type = external_identity

            if captcha.active:
                captcha_status, captcha_message = self.validate_captcha(
                    captcha.private_key)

                if not captcha_status:
                    _value = form_result
                    _msg = _('Bad captcha')
                    error_dict = {'recaptcha_field': captcha_message}
                    raise formencode.Invalid(
                        _msg, _value, None, error_dict=error_dict)

            new_user = UserModel().create_registration(
                form_result, extern_name=extern_name, extern_type=extern_type)

            action_data = {'data': new_user.get_api_data(),
                           'user_agent': self.request.user_agent}

            if external_identity:
                action_data['external_identity'] = external_identity

            audit_user = audit_logger.UserWrap(
                username=new_user.username,
                user_id=new_user.user_id,
                ip_addr=self.request.remote_addr)

            audit_logger.store_web(
                'user.register', action_data=action_data,
                user=audit_user)

            event = UserRegistered(user=new_user, session=self.session)
            trigger(event)
            h.flash(
                _('You have successfully registered with RhodeCode. You can log-in now.'),
                category='success')
            if external_identity:
                h.flash(
                    _('Please use the {identity} button to log-in').format(
                        identity=external_identity),
                    category='success')
            Session().commit()

            redirect_ro = self.request.route_path('login')
            raise HTTPFound(redirect_ro)

        except formencode.Invalid as errors:
            errors.value.pop('password', None)
            errors.value.pop('password_confirmation', None)
            return self.register(
                defaults=errors.value, errors=errors.error_dict)

        except UserCreationError as e:
            # container auth or other auth functions that create users on
            # the fly can throw this exception signaling that there's issue
            # with user creation, explanation should be provided in
            # Exception itself
            h.flash(e, category='error')
            return self.register()

    def password_reset(self):
        c = self.load_default_context()
        captcha = self._get_captcha_data()

        template_context = {
            'captcha_active': captcha.active,
            'captcha_public_key': captcha.public_key,
            'defaults': {},
            'errors': {},
        }

        # always send implicit message to prevent from discovery of
        # matching emails
        msg = _('If such email exists, a password reset link was sent to it.')

        def default_response():
            log.debug('faking response on invalid password reset')
            # make this take 2s, to prevent brute forcing.
            time.sleep(2)
            h.flash(msg, category='success')
            return HTTPFound(self.request.route_path('reset_password'))

        if self.request.POST:
            if h.HasPermissionAny('hg.password_reset.disabled')():
                _email = self.request.POST.get('email', '')
                log.error('Failed attempt to reset password for `%s`.', _email)
                h.flash(_('Password reset has been disabled.'), category='error')
                return HTTPFound(self.request.route_path('reset_password'))

            password_reset_form = PasswordResetForm(self.request.translate)()
            description = u'Generated token for password reset from {}'.format(
                datetime.datetime.now().isoformat())

            try:
                form_result = password_reset_form.to_python(
                    self.request.POST)
                user_email = form_result['email']

                if captcha.active:
                    captcha_status, captcha_message = self.validate_captcha(
                        captcha.private_key)

                    if not captcha_status:
                        _value = form_result
                        _msg = _('Bad captcha')
                        error_dict = {'recaptcha_field': captcha_message}
                        raise formencode.Invalid(
                            _msg, _value, None, error_dict=error_dict)

                # Generate reset URL and send mail.
                user = User.get_by_email(user_email)

                # only allow rhodecode based users to reset their password
                # external auth shouldn't allow password reset
                if user and user.extern_type != auth_rhodecode.RhodeCodeAuthPlugin.uid:
                    log.warning('User %s with external type `%s` tried a password reset. '
                                'This try was rejected', user, user.extern_type)
                    return default_response()

                # generate password reset token that expires in 10 minutes
                reset_token = UserModel().add_auth_token(
                    user=user, lifetime_minutes=10,
                    role=UserModel.auth_token_role.ROLE_PASSWORD_RESET,
                    description=description)
                Session().commit()

                log.debug('Successfully created password recovery token')
                password_reset_url = self.request.route_url(
                    'reset_password_confirmation',
                    _query={'key': reset_token.api_key})
                UserModel().reset_password_link(
                    form_result, password_reset_url)

                action_data = {'email': user_email,
                               'user_agent': self.request.user_agent}
                audit_logger.store_web(
                    'user.password.reset_request', action_data=action_data,
                    user=self._rhodecode_user, commit=True)

                return default_response()

            except formencode.Invalid as errors:
                template_context.update({
                    'defaults': errors.value,
                    'errors': errors.error_dict,
                })
                if not self.request.POST.get('email'):
                    # case of empty email, we want to report that
                    return self._get_template_context(c, **template_context)

                if 'recaptcha_field' in errors.error_dict:
                    # case of failed captcha
                    return self._get_template_context(c, **template_context)

            return default_response()

        return self._get_template_context(c, **template_context)

    def password_reset_confirmation(self):
        self.load_default_context()
        if self.request.GET and self.request.GET.get('key'):
            # make this take 2s, to prevent brute forcing.
            time.sleep(2)

            token = AuthTokenModel().get_auth_token(
                self.request.GET.get('key'))

            # verify token is the correct role
            if token is None or token.role != UserApiKeys.ROLE_PASSWORD_RESET:
                log.debug('Got token with role:%s expected is %s',
                          getattr(token, 'role', 'EMPTY_TOKEN'),
                          UserApiKeys.ROLE_PASSWORD_RESET)
                h.flash(
                    _('Given reset token is invalid'), category='error')
                return HTTPFound(self.request.route_path('reset_password'))

            try:
                owner = token.user
                data = {'email': owner.email, 'token': token.api_key}
                UserModel().reset_password(data)
                h.flash(
                    _('Your password reset was successful, '
                      'a new password has been sent to your email'),
                    category='success')
            except Exception as e:
                log.error(e)
                return HTTPFound(self.request.route_path('reset_password'))

        return HTTPFound(self.request.route_path('login'))
