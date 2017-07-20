# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017  RhodeCode GmbH
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

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.response import Response

from rhodecode.apps._base import BaseAppView

from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired)
from rhodecode.model.db import User, UserIpMap
from rhodecode.model.forms import (
    ApplicationPermissionsForm, ObjectPermissionsForm, UserPermissionsForm)
from rhodecode.model.meta import Session
from rhodecode.model.permission import PermissionModel
from rhodecode.model.settings import SettingsModel


log = logging.getLogger(__name__)


class AdminPermissionsView(BaseAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()

        self._register_global_c(c)
        PermissionModel().set_global_permission_choices(
            c, gettext_translator=self.request.translate)
        return c

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_permissions_application', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')
    def permissions_application(self):
        c = self.load_default_context()
        c.active = 'application'

        c.user = User.get_default_user(refresh=True)

        app_settings = SettingsModel().get_all_settings()
        defaults = {
            'anonymous': c.user.active,
            'default_register_message': app_settings.get(
                'rhodecode_register_message')
        }
        defaults.update(c.user.get_default_perms())

        data = render('rhodecode:templates/admin/permissions/permissions.mako',
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
        route_name='admin_permissions_application_update', request_method='POST',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')
    def permissions_application_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'application'

        _form = ApplicationPermissionsForm(
            [x[0] for x in c.register_choices],
            [x[0] for x in c.password_reset_choices],
            [x[0] for x in c.extern_activate_choices])()

        try:
            form_result = _form.to_python(dict(self.request.POST))
            form_result.update({'perm_user_name': User.DEFAULT_USER})
            PermissionModel().update_application_permissions(form_result)

            settings = [
                ('register_message', 'default_register_message'),
            ]
            for setting, form_key in settings:
                sett = SettingsModel().create_or_update_setting(
                    setting, form_result[form_key])
                Session().add(sett)

            Session().commit()
            h.flash(_('Application permissions updated successfully'),
                    category='success')

        except formencode.Invalid as errors:
            defaults = errors.value

            data = render(
                'rhodecode:templates/admin/permissions/permissions.mako',
                self._get_template_context(c), self.request)
            html = formencode.htmlfill.render(
                data,
                defaults=defaults,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False
            )
            return Response(html)

        except Exception:
            log.exception("Exception during update of permissions")
            h.flash(_('Error occurred during update of permissions'),
                    category='error')

        raise HTTPFound(h.route_path('admin_permissions_application'))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_permissions_object', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')
    def permissions_objects(self):
        c = self.load_default_context()
        c.active = 'objects'

        c.user = User.get_default_user(refresh=True)
        defaults = {}
        defaults.update(c.user.get_default_perms())

        data = render(
            'rhodecode:templates/admin/permissions/permissions.mako',
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
        route_name='admin_permissions_object_update', request_method='POST',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')
    def permissions_objects_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'objects'

        _form = ObjectPermissionsForm(
            [x[0] for x in c.repo_perms_choices],
            [x[0] for x in c.group_perms_choices],
            [x[0] for x in c.user_group_perms_choices])()

        try:
            form_result = _form.to_python(dict(self.request.POST))
            form_result.update({'perm_user_name': User.DEFAULT_USER})
            PermissionModel().update_object_permissions(form_result)

            Session().commit()
            h.flash(_('Object permissions updated successfully'),
                    category='success')

        except formencode.Invalid as errors:
            defaults = errors.value

            data = render(
                'rhodecode:templates/admin/permissions/permissions.mako',
                self._get_template_context(c), self.request)
            html = formencode.htmlfill.render(
                data,
                defaults=defaults,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False
            )
            return Response(html)
        except Exception:
            log.exception("Exception during update of permissions")
            h.flash(_('Error occurred during update of permissions'),
                    category='error')

        raise HTTPFound(h.route_path('admin_permissions_object'))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_permissions_global', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')
    def permissions_global(self):
        c = self.load_default_context()
        c.active = 'global'

        c.user = User.get_default_user(refresh=True)
        defaults = {}
        defaults.update(c.user.get_default_perms())

        data = render(
            'rhodecode:templates/admin/permissions/permissions.mako',
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
        route_name='admin_permissions_global_update', request_method='POST',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')
    def permissions_global_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'global'

        _form = UserPermissionsForm(
            [x[0] for x in c.repo_create_choices],
            [x[0] for x in c.repo_create_on_write_choices],
            [x[0] for x in c.repo_group_create_choices],
            [x[0] for x in c.user_group_create_choices],
            [x[0] for x in c.fork_choices],
            [x[0] for x in c.inherit_default_permission_choices])()

        try:
            form_result = _form.to_python(dict(self.request.POST))
            form_result.update({'perm_user_name': User.DEFAULT_USER})
            PermissionModel().update_user_permissions(form_result)

            Session().commit()
            h.flash(_('Global permissions updated successfully'),
                    category='success')

        except formencode.Invalid as errors:
            defaults = errors.value

            data = render(
                'rhodecode:templates/admin/permissions/permissions.mako',
                self._get_template_context(c), self.request)
            html = formencode.htmlfill.render(
                data,
                defaults=defaults,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False
            )
            return Response(html)
        except Exception:
            log.exception("Exception during update of permissions")
            h.flash(_('Error occurred during update of permissions'),
                    category='error')

        raise HTTPFound(h.route_path('admin_permissions_global'))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_permissions_ips', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')
    def permissions_ips(self):
        c = self.load_default_context()
        c.active = 'ips'

        c.user = User.get_default_user(refresh=True)
        c.user_ip_map = (
            UserIpMap.query().filter(UserIpMap.user == c.user).all())

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_permissions_overview', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')
    def permissions_overview(self):
        c = self.load_default_context()
        c.active = 'perms'

        c.user = User.get_default_user(refresh=True)
        c.perm_user = c.user.AuthUser
        return self._get_template_context(c)
