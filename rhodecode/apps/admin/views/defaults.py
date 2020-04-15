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

import logging

import formencode
import formencode.htmlfill

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.response import Response

from rhodecode.apps._base import BaseAppView
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired)
from rhodecode.lib import helpers as h
from rhodecode.model.forms import DefaultsForm
from rhodecode.model.meta import Session
from rhodecode import BACKENDS
from rhodecode.model.settings import SettingsModel

log = logging.getLogger(__name__)


class AdminDefaultSettingsView(BaseAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()


        return c

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_defaults_repositories', request_method='GET',
        renderer='rhodecode:templates/admin/defaults/defaults.mako')
    def defaults_repository_show(self):
        c = self.load_default_context()
        c.backends = BACKENDS.keys()
        c.active = 'repositories'
        defaults = SettingsModel().get_default_repo_settings()

        data = render(
            'rhodecode:templates/admin/defaults/defaults.mako',
            self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_defaults_repositories_update', request_method='POST',
        renderer='rhodecode:templates/admin/defaults/defaults.mako')
    def defaults_repository_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'repositories'
        form = DefaultsForm(self.request.translate)()

        try:
            form_result = form.to_python(dict(self.request.POST))
            for k, v in form_result.iteritems():
                setting = SettingsModel().create_or_update_setting(k, v)
                Session().add(setting)
            Session().commit()
            h.flash(_('Default settings updated successfully'),
                    category='success')

        except formencode.Invalid as errors:
            data = render(
                'rhodecode:templates/admin/defaults/defaults.mako',
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
            log.exception('Exception in update action')
            h.flash(_('Error occurred during update of default values'),
                    category='error')

        raise HTTPFound(h.route_path('admin_defaults_repositories'))
