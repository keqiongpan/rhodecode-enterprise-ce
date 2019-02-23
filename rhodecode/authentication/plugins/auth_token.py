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

"""
RhodeCode authentication token plugin for built in internal auth
"""

import logging
import colander

from rhodecode.authentication.schema import AuthnPluginSettingsSchemaBase
from rhodecode.translation import _
from rhodecode.authentication.base import (
    RhodeCodeAuthPluginBase, VCS_TYPE, hybrid_property)
from rhodecode.authentication.routes import AuthnPluginResourceBase
from rhodecode.model.db import User, UserApiKeys, Repository


log = logging.getLogger(__name__)


def plugin_factory(plugin_id, *args, **kwargs):
    plugin = RhodeCodeAuthPlugin(plugin_id)
    return plugin


class RhodecodeAuthnResource(AuthnPluginResourceBase):
    pass


class RhodeCodeAuthPlugin(RhodeCodeAuthPluginBase):
    """
    Enables usage of authentication tokens for vcs operations.
    """
    uid = 'token'
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
        return _('Rhodecode Token')

    @classmethod
    def docs(cls):
        return "https://docs.rhodecode.com/RhodeCode-Enterprise/auth/auth-token.html"

    @hybrid_property
    def name(self):
        return u"authtoken"

    def user_activation_state(self):
        def_user_perms = User.get_default_user().AuthUser().permissions['global']
        return 'hg.register.auto_activate' in def_user_perms

    def allows_authentication_from(
            self, user, allows_non_existing_user=True,
            allowed_auth_plugins=None, allowed_auth_sources=None):
        """
        Custom method for this auth that doesn't accept empty users. And also
        allows users from all other active plugins to use it and also
        authenticate against it. But only via vcs mode
        """
        from rhodecode.authentication.base import get_authn_registry
        authn_registry = get_authn_registry()

        active_plugins = set(
            [x.name for x in authn_registry.get_plugins_for_authentication()])
        active_plugins.discard(self.name)

        allowed_auth_plugins = [self.name] + list(active_plugins)
        # only for vcs operations
        allowed_auth_sources = [VCS_TYPE]

        return super(RhodeCodeAuthPlugin, self).allows_authentication_from(
            user, allows_non_existing_user=False,
            allowed_auth_plugins=allowed_auth_plugins,
            allowed_auth_sources=allowed_auth_sources)

    def auth(self, userobj, username, password, settings, **kwargs):
        if not userobj:
            log.debug('userobj was:%s skipping', userobj)
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

        log.debug('Authenticating user with args %s', user_attrs)
        if userobj.active:
            # calling context repo for token scopes
            scope_repo_id = None
            if self.acl_repo_name:
                repo = Repository.get_by_repo_name(self.acl_repo_name)
                scope_repo_id = repo.repo_id if repo else None

            token_match = userobj.authenticate_by_token(
                password, roles=[UserApiKeys.ROLE_VCS],
                scope_repo_id=scope_repo_id)

            if userobj.username == username and token_match:
                log.info(
                    'user `%s` successfully authenticated via %s',
                    user_attrs['username'], self.name)
                return user_attrs
            log.warning('user `%s` failed to authenticate via %s, reason: bad or '
                        'inactive token.', username, self.name)
        else:
            log.warning('user `%s` failed to authenticate via %s, reason: account not '
                        'active.', username, self.name)
        return None


def includeme(config):
    plugin_id = 'egg:rhodecode-enterprise-ce#{}'.format(RhodeCodeAuthPlugin.uid)
    plugin_factory(plugin_id).includeme(config)


class RhodeCodeSettingsSchema(AuthnPluginSettingsSchemaBase):
    auth_scope_choices = [
        (RhodeCodeAuthPlugin.AUTH_RESTRICTION_SCOPE_VCS, 'VCS only'),
    ]

    scope_restriction = colander.SchemaNode(
        colander.String(),
        default=auth_scope_choices[0],
        description=_('Choose operation scope restriction when authenticating.'),
        title=_('Scope restriction'),
        validator=colander.OneOf([x[0] for x in auth_scope_choices]),
        widget='select_with_labels',
        choices=auth_scope_choices
    )
