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

import colander
import formencode.htmlfill
import logging

from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.response import Response

from rhodecode.apps._base import BaseAppView
from rhodecode.authentication.base import get_authn_registry
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired)
from rhodecode.lib.caches import clear_cache_manager
from rhodecode.model.forms import AuthSettingsForm
from rhodecode.model.meta import Session
from rhodecode.model.settings import SettingsModel

log = logging.getLogger(__name__)


class AuthnPluginViewBase(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        self.plugin = self.context.plugin
        return c

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def settings_get(self, defaults=None, errors=None):
        """
        View that displays the plugin settings as a form.
        """
        c = self.load_default_context()
        defaults = defaults or {}
        errors = errors or {}
        schema = self.plugin.get_settings_schema()

        # Compute default values for the form. Priority is:
        # 1. Passed to this method 2. DB value 3. Schema default
        for node in schema:
            if node.name not in defaults:
                defaults[node.name] = self.plugin.get_setting_by_name(
                    node.name, node.default)

        template_context = {
            'defaults': defaults,
            'errors': errors,
            'plugin': self.context.plugin,
            'resource': self.context,
        }

        return self._get_template_context(c, **template_context)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def settings_post(self):
        """
        View that validates and stores the plugin settings.
        """
        _ = self.request.translate
        self.load_default_context()
        schema = self.plugin.get_settings_schema()
        data = self.request.params

        try:
            valid_data = schema.deserialize(data)
        except colander.Invalid as e:
            # Display error message and display form again.
            h.flash(
                _('Errors exist when saving plugin settings. '
                  'Please check the form inputs.'),
                category='error')
            defaults = {key: data[key] for key in data if key in schema}
            return self.settings_get(errors=e.asdict(), defaults=defaults)

        # Store validated data.
        for name, value in valid_data.items():
            self.plugin.create_or_update_setting(name, value)
        Session().commit()

        # Display success message and redirect.
        h.flash(_('Auth settings updated successfully.'), category='success')
        redirect_to = self.request.resource_path(
            self.context, route_name='auth_home')
        return HTTPFound(redirect_to)


class AuthSettingsView(BaseAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def index(self, defaults=None, errors=None, prefix_error=False):
        c = self.load_default_context()

        defaults = defaults or {}
        authn_registry = get_authn_registry(self.request.registry)
        enabled_plugins = SettingsModel().get_auth_plugins()

        # Create template context and render it.
        template_context = {
            'resource': self.context,
            'available_plugins': authn_registry.get_plugins(),
            'enabled_plugins': enabled_plugins,
        }
        html = render('rhodecode:templates/admin/auth/auth_settings.mako',
                      self._get_template_context(c, **template_context),
                      self.request)

        # Create form default values and fill the form.
        form_defaults = {
            'auth_plugins': ',\n'.join(enabled_plugins)
        }
        form_defaults.update(defaults)
        html = formencode.htmlfill.render(
            html,
            defaults=form_defaults,
            errors=errors,
            prefix_error=prefix_error,
            encoding="UTF-8",
            force_defaults=False)

        return Response(html)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def auth_settings(self):
        _ = self.request.translate
        try:
            form = AuthSettingsForm(self.request.translate)()
            form_result = form.to_python(self.request.POST)
            plugins = ','.join(form_result['auth_plugins'])
            setting = SettingsModel().create_or_update_setting(
                'auth_plugins', plugins)
            Session().add(setting)
            Session().commit()

            h.flash(_('Auth settings updated successfully.'), category='success')
        except formencode.Invalid as errors:
            e = errors.error_dict or {}
            h.flash(_('Errors exist when saving plugin setting. '
                      'Please check the form inputs.'), category='error')
            return self.index(
                defaults=errors.value,
                errors=e,
                prefix_error=False)
        except Exception:
            log.exception('Exception in auth_settings')
            h.flash(_('Error occurred during update of auth settings.'),
                    category='error')

        redirect_to = self.request.resource_path(
            self.context, route_name='auth_home')
        return HTTPFound(redirect_to)
