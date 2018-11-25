# -*- coding: utf-8 -*-

# Copyright (C) 2012-2018 RhodeCode GmbH
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
import importlib

from pyramid.authentication import SessionAuthenticationPolicy

from rhodecode.authentication.registry import AuthenticationPluginRegistry
from rhodecode.authentication.routes import root_factory
from rhodecode.authentication.routes import AuthnRootResource
from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.model.settings import SettingsModel

log = logging.getLogger(__name__)

legacy_plugin_prefix = 'py:'
plugin_default_auth_ttl = 30


def _import_legacy_plugin(plugin_id):
    module_name = plugin_id.split(legacy_plugin_prefix, 1)[-1]
    module = importlib.import_module(module_name)
    return module.plugin_factory(plugin_id=plugin_id)


def discover_legacy_plugins(config, prefix=legacy_plugin_prefix):
    """
    Function that imports the legacy plugins stored in the 'auth_plugins'
    setting in database which are using the specified prefix. Normally 'py:' is
    used for the legacy plugins.
    """
    log.debug('authentication: running legacy plugin discovery for prefix %s',
              legacy_plugin_prefix)
    try:
        auth_plugins = SettingsModel().get_setting_by_name('auth_plugins')
        enabled_plugins = auth_plugins.app_settings_value
        legacy_plugins = [id_ for id_ in enabled_plugins if id_.startswith(prefix)]
    except Exception:
        legacy_plugins = []

    for plugin_id in legacy_plugins:
        log.debug('Legacy plugin discovered: "%s"', plugin_id)
        try:
            plugin = _import_legacy_plugin(plugin_id)
            config.include(plugin.includeme)
        except Exception as e:
            log.exception(
                'Exception while loading legacy authentication plugin '
                '"{}": {}'.format(plugin_id, e.message))


def includeme(config):
    # Set authentication policy.
    authn_policy = SessionAuthenticationPolicy()
    config.set_authentication_policy(authn_policy)

    # Create authentication plugin registry and add it to the pyramid registry.
    authn_registry = AuthenticationPluginRegistry(config.get_settings())
    config.add_directive('add_authn_plugin', authn_registry.add_authn_plugin)
    config.registry.registerUtility(authn_registry)

    # Create authentication traversal root resource.
    authn_root_resource = root_factory()
    config.add_directive('add_authn_resource',
                         authn_root_resource.add_authn_resource)

    # Add the authentication traversal route.
    config.add_route('auth_home',
                     ADMIN_PREFIX + '/auth*traverse',
                     factory=root_factory)
    # Add the authentication settings root views.
    config.add_view('rhodecode.authentication.views.AuthSettingsView',
                    attr='index',
                    request_method='GET',
                    route_name='auth_home',
                    context=AuthnRootResource)
    config.add_view('rhodecode.authentication.views.AuthSettingsView',
                    attr='auth_settings',
                    request_method='POST',
                    route_name='auth_home',
                    context=AuthnRootResource)
