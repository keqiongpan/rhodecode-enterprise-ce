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

import collections
import logging

from pylons import tmpl_context as c
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from rhodecode.translation import _
from rhodecode.svn_support.utils import generate_mod_dav_svn_config

from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired)
from rhodecode.lib.utils import read_opensource_licenses
from rhodecode.lib.utils2 import safe_int
from rhodecode.lib import system_info
from rhodecode.lib import user_sessions


from .navigation import navigation_list


log = logging.getLogger(__name__)


class AdminSettingsView(object):

    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.session = request.session
        self._rhodecode_user = request.user

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_open_source', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def open_source_licenses(self):
        c.active = 'open_source'
        c.navlist = navigation_list(self.request)
        c.opensource_licenses = collections.OrderedDict(
            sorted(read_opensource_licenses().items(), key=lambda t: t[0]))

        return {}

    @LoginRequired()
    @CSRFRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_vcs_svn_generate_cfg',
        request_method='POST', renderer='json')
    def vcs_svn_generate_config(self):
        try:
            generate_mod_dav_svn_config(self.request.registry)
            msg = {
                'message': _('Apache configuration for Subversion generated.'),
                'level': 'success',
            }
        except Exception:
            log.exception(
                'Exception while generating the Apache '
                'configuration for Subversion.')
            msg = {
                'message': _('Failed to generate the Apache configuration for Subversion.'),
                'level': 'error',
            }

        data = {'message': msg}
        return data

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_sessions', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def settings_sessions(self):
        c.active = 'sessions'
        c.navlist = navigation_list(self.request)

        c.cleanup_older_days = 60
        older_than_seconds = 24 * 60 * 60 * 24 * c.cleanup_older_days

        config = system_info.rhodecode_config().get_value()['value']['config']
        c.session_model = user_sessions.get_session_handler(
            config.get('beaker.session.type', 'memory'))(config)

        c.session_conf = c.session_model.config
        c.session_count = c.session_model.get_count()
        c.session_expired_count = c.session_model.get_expired_count(
            older_than_seconds)

        return {}

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_sessions_cleanup', request_method='POST')
    def settings_sessions_cleanup(self):

        expire_days = safe_int(self.request.params.get('expire_days'))

        if expire_days is None:
            expire_days = 60

        older_than_seconds = 24 * 60 * 60 * 24 * expire_days

        config = system_info.rhodecode_config().get_value()['value']['config']
        session_model = user_sessions.get_session_handler(
            config.get('beaker.session.type', 'memory'))(config)

        try:
            session_model.clean_sessions(
                older_than_seconds=older_than_seconds)
            self.request.session.flash(
                _('Cleaned up old sessions'), queue='success')
        except user_sessions.CleanupCommand as msg:
            self.request.session.flash(msg, category='warning')
        except Exception as e:
            log.exception('Failed session cleanup')
            self.request.session.flash(
                _('Failed to cleanup up old sessions'), queue='error')

        redirect_to = self.request.resource_path(
            self.context, route_name='admin_settings_sessions')
        return HTTPFound(redirect_to)
