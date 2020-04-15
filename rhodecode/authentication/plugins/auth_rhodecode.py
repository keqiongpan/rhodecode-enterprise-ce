# -*- coding: utf-8 -*-

# Copyright (C) 2012-2020 RhodeCode GmbH
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

"""
RhodeCode authentication plugin for built in internal auth
"""

import logging

import colander

from rhodecode.translation import _
from rhodecode.lib.utils2 import safe_str
from rhodecode.model.db import User
from rhodecode.authentication.schema import AuthnPluginSettingsSchemaBase
from rhodecode.authentication.base import (
    RhodeCodeAuthPluginBase, hybrid_property, HTTP_TYPE, VCS_TYPE)
from rhodecode.authentication.routes import AuthnPluginResourceBase

log = logging.getLogger(__name__)


def plugin_factory(plugin_id, *args, **kwargs):
    plugin = RhodeCodeAuthPlugin(plugin_id)
    return plugin


class RhodecodeAuthnResource(AuthnPluginResourceBase):
    pass


class RhodeCodeAuthPlugin(RhodeCodeAuthPluginBase):
    uid = 'rhodecode'
    AUTH_RESTRICTION_NONE = 'user_all'
    AUTH_RESTRICTION_SUPER_ADMIN = 'user_super_admin'
    AUTH_RESTRICTION_SCOPE_ALL = 'scope_all'
    AUTH_RESTRICTION_SCOPE_HTTP = 'scope_http'
    AUTH_RESTRICTION_SCOPE_VCS = 'scope_vcs'

    def includeme(self, config):
        config.add_authn_plugin(self)
        config.add_authn_resource(self.get_id(), RhodecodeAuthnResource(self))
        config.add_view(
            'rhodecode.authentication.views.AuthnPluginViewBase',
            attr='settings_get',
            renderer='rhodecode:templates/admin/auth/plugin_settings.mako',
            request_method='GET',
            route_name='auth_home',
            context=RhodecodeAuthnResource)
        config.add_view(
            'rhodecode.authentication.views.AuthnPluginViewBase',
            attr='settings_post',
            renderer='rhodecode:templates/admin/auth/plugin_settings.mako',
            request_method='POST',
            route_name='auth_home',
            context=RhodecodeAuthnResource)

    def get_settings_schema(self):
        return RhodeCodeSettingsSchema()

    def get_display_name(self):
        return _('RhodeCode Internal')

    @classmethod
    def docs(cls):
        return "https://docs.rhodecode.com/RhodeCode-Enterprise/auth/auth.html"

    @hybrid_property
    def name(self):
        return u"rhodecode"

    def user_activation_state(self):
        def_user_perms = User.get_default_user().AuthUser().permissions['global']
        return 'hg.register.auto_activate' in def_user_perms

    def allows_authentication_from(
            self, user, allows_non_existing_user=True,
            allowed_auth_plugins=None, allowed_auth_sources=None):
        """
        Custom method for this auth that doesn't accept non existing users.
        We know that user exists in our database.
        """
        allows_non_existing_user = False
        return super(RhodeCodeAuthPlugin, self).allows_authentication_from(
            user, allows_non_existing_user=allows_non_existing_user)

    def auth(self, userobj, username, password, settings, **kwargs):
        if not userobj:
            log.debug('userobj was:%s skipping', userobj)
            return None

        if userobj.extern_type != self.name:
            log.warning("userobj:%s extern_type mismatch got:`%s` expected:`%s`",
                        userobj, userobj.extern_type, self.name)
            return None

        # check scope of auth
        scope_restriction = settings.get('scope_restriction', '')

        if scope_restriction == self.AUTH_RESTRICTION_SCOPE_HTTP \
                and self.auth_type != HTTP_TYPE:
            log.warning("userobj:%s tried scope type %s and scope restriction is set to %s",
                        userobj, self.auth_type, scope_restriction)
            return None

        if scope_restriction == self.AUTH_RESTRICTION_SCOPE_VCS \
                and self.auth_type != VCS_TYPE:
            log.warning("userobj:%s tried scope type %s and scope restriction is set to %s",
                        userobj, self.auth_type, scope_restriction)
            return None

        # check super-admin restriction
        auth_restriction = settings.get('auth_restriction', '')

        if auth_restriction == self.AUTH_RESTRICTION_SUPER_ADMIN \
                and userobj.admin is False:
            log.warning("userobj:%s is not super-admin and auth restriction is set to %s",
                        userobj, auth_restriction)
            return None

        user_attrs = {
            "username": userobj.username,
            "firstname": userobj.firstname,
            "lastname": userobj.lastname,
            "groups": [],
            'user_group_sync': False,
            "email": userobj.email,
            "admin": userobj.admin,
            "active": userobj.active,
            "active_from_extern": userobj.active,
            "extern_name": userobj.user_id,
            "extern_type": userobj.extern_type,
        }

        log.debug("User attributes:%s", user_attrs)
        if userobj.active:
            from rhodecode.lib import auth
            crypto_backend = auth.crypto_backend()
            password_encoded = safe_str(password)
            password_match, new_hash = crypto_backend.hash_check_with_upgrade(
                password_encoded, userobj.password or '')

            if password_match and new_hash:
                log.debug('user %s properly authenticated, but '
                          'requires hash change to bcrypt', userobj)
                # if password match, and we use OLD deprecated hash,
                # we should migrate this user hash password to the new hash
                # we store the new returned by hash_check_with_upgrade function
                user_attrs['_hash_migrate'] = new_hash

            if userobj.username == User.DEFAULT_USER and userobj.active:
                log.info('user `%s` authenticated correctly as anonymous user',
                         userobj.username)
                return user_attrs

            elif userobj.username == username and password_match:
                log.info('user `%s` authenticated correctly', userobj.username)
                return user_attrs
            log.warning("user `%s` used a wrong password when "
                        "authenticating on this plugin", userobj.username)
            return None
        else:
            log.warning('user `%s` failed to authenticate via %s, reason: account not '
                        'active.', username, self.name)
            return None


class RhodeCodeSettingsSchema(AuthnPluginSettingsSchemaBase):

    auth_restriction_choices = [
        (RhodeCodeAuthPlugin.AUTH_RESTRICTION_NONE, 'All users'),
        (RhodeCodeAuthPlugin.AUTH_RESTRICTION_SUPER_ADMIN, 'Super admins only'),
    ]

    auth_scope_choices = [
        (RhodeCodeAuthPlugin.AUTH_RESTRICTION_SCOPE_ALL, 'HTTP and VCS'),
        (RhodeCodeAuthPlugin.AUTH_RESTRICTION_SCOPE_HTTP, 'HTTP only'),
    ]

    auth_restriction = colander.SchemaNode(
        colander.String(),
        default=auth_restriction_choices[0],
        description=_('Allowed user types for authentication using this plugin.'),
        title=_('User restriction'),
        validator=colander.OneOf([x[0] for x in auth_restriction_choices]),
        widget='select_with_labels',
        choices=auth_restriction_choices
    )
    scope_restriction = colander.SchemaNode(
        colander.String(),
        default=auth_scope_choices[0],
        description=_('Allowed protocols for authentication using this plugin. '
                      'VCS means GIT/HG/SVN. HTTP is web based login.'),
        title=_('Scope restriction'),
        validator=colander.OneOf([x[0] for x in auth_scope_choices]),
        widget='select_with_labels',
        choices=auth_scope_choices
    )


def includeme(config):
    plugin_id = 'egg:rhodecode-enterprise-ce#{}'.format(RhodeCodeAuthPlugin.uid)
    plugin_factory(plugin_id).includeme(config)
