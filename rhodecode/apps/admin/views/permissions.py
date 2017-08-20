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

import re
import logging
import formencode
import datetime
from pyramid.interfaces import IRoutesMapper

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.response import Response

from rhodecode.apps._base import BaseAppView, DataGridAppView
from rhodecode.apps.ssh_support import SshKeyFileChangeEvent
from rhodecode.events import trigger

from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired)
from rhodecode.lib.utils2 import aslist, safe_unicode
from rhodecode.model.db import or_, joinedload, coalesce, User, UserIpMap, UserSshKeys
from rhodecode.model.forms import (
    ApplicationPermissionsForm, ObjectPermissionsForm, UserPermissionsForm)
from rhodecode.model.meta import Session
from rhodecode.model.permission import PermissionModel
from rhodecode.model.settings import SettingsModel


log = logging.getLogger(__name__)


class AdminPermissionsView(BaseAppView, DataGridAppView):
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
        c.perm_user = c.user.AuthUser()
        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_permissions_auth_token_access', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')
    def auth_token_access(self):
        from rhodecode import CONFIG

        c = self.load_default_context()
        c.active = 'auth_token_access'

        c.user = User.get_default_user(refresh=True)
        c.perm_user = c.user.AuthUser()

        mapper = self.request.registry.queryUtility(IRoutesMapper)
        c.view_data = []

        _argument_prog = re.compile('\{(.*?)\}|:\((.*)\)')
        introspector = self.request.registry.introspector

        view_intr = {}
        for view_data in introspector.get_category('views'):
            intr = view_data['introspectable']

            if 'route_name' in intr and intr['attr']:
                view_intr[intr['route_name']] = '{}:{}'.format(
                    str(intr['derived_callable'].func_name), intr['attr']
                )

        c.whitelist_key = 'api_access_controllers_whitelist'
        c.whitelist_file = CONFIG.get('__file__')
        whitelist_views = aslist(
            CONFIG.get(c.whitelist_key), sep=',')

        for route_info in mapper.get_routes():
            if not route_info.name.startswith('__'):
                routepath = route_info.pattern

                def replace(matchobj):
                    if matchobj.group(1):
                        return "{%s}" % matchobj.group(1).split(':')[0]
                    else:
                        return "{%s}" % matchobj.group(2)

                routepath = _argument_prog.sub(replace, routepath)

                if not routepath.startswith('/'):
                    routepath = '/' + routepath

                view_fqn = view_intr.get(route_info.name, 'NOT AVAILABLE')
                active = view_fqn in whitelist_views
                c.view_data.append((route_info.name, view_fqn, routepath, active))

        c.whitelist_views = whitelist_views
        return self._get_template_context(c)

    def ssh_enabled(self):
        return self.request.registry.settings.get(
            'ssh.generate_authorized_keyfile')

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_permissions_ssh_keys', request_method='GET',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')
    def ssh_keys(self):
        c = self.load_default_context()
        c.active = 'ssh_keys'
        c.ssh_enabled = self.ssh_enabled()
        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_permissions_ssh_keys_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def ssh_keys_data(self):
        _ = self.request.translate
        column_map = {
            'fingerprint': 'ssh_key_fingerprint',
            'username': User.username
        }
        draw, start, limit = self._extract_chunk(self.request)
        search_q, order_by, order_dir = self._extract_ordering(
            self.request, column_map=column_map)

        ssh_keys_data_total_count = UserSshKeys.query()\
            .count()

        # json generate
        base_q = UserSshKeys.query().join(UserSshKeys.user)

        if search_q:
            like_expression = u'%{}%'.format(safe_unicode(search_q))
            base_q = base_q.filter(or_(
                User.username.ilike(like_expression),
                UserSshKeys.ssh_key_fingerprint.ilike(like_expression),
            ))

        users_data_total_filtered_count = base_q.count()

        sort_col = self._get_order_col(order_by, UserSshKeys)
        if sort_col:
            if order_dir == 'asc':
                # handle null values properly to order by NULL last
                if order_by in ['created_on']:
                    sort_col = coalesce(sort_col, datetime.date.max)
                sort_col = sort_col.asc()
            else:
                # handle null values properly to order by NULL last
                if order_by in ['created_on']:
                    sort_col = coalesce(sort_col, datetime.date.min)
                sort_col = sort_col.desc()

        base_q = base_q.order_by(sort_col)
        base_q = base_q.offset(start).limit(limit)

        ssh_keys = base_q.all()

        ssh_keys_data = []
        for ssh_key in ssh_keys:
            ssh_keys_data.append({
                "username": h.gravatar_with_user(self.request, ssh_key.user.username),
                "fingerprint": ssh_key.ssh_key_fingerprint,
                "description": ssh_key.description,
                "created_on": h.format_date(ssh_key.created_on),
                "action": h.link_to(
                    _('Edit'), h.route_path('edit_user_ssh_keys',
                                            user_id=ssh_key.user.user_id))
            })

        data = ({
            'draw': draw,
            'data': ssh_keys_data,
            'recordsTotal': ssh_keys_data_total_count,
            'recordsFiltered': users_data_total_filtered_count,
        })

        return data

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_permissions_ssh_keys_update', request_method='POST',
        renderer='rhodecode:templates/admin/permissions/permissions.mako')
    def ssh_keys_update(self):
        _ = self.request.translate
        self.load_default_context()

        ssh_enabled = self.ssh_enabled()
        key_file = self.request.registry.settings.get(
            'ssh.authorized_keys_file_path')
        if ssh_enabled:
            trigger(SshKeyFileChangeEvent(), self.request.registry)
            h.flash(_('Updated SSH keys file: {}').format(key_file),
                    category='success')
        else:
            h.flash(_('SSH key support is disabled in .ini file'),
                    category='warning')

        raise HTTPFound(h.route_path('admin_permissions_ssh_keys'))
