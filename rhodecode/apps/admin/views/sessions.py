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


from pyramid.httpexceptions import HTTPFound

from rhodecode.apps._base import BaseAppView
from rhodecode.apps._base.navigation import navigation_list
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired)
from rhodecode.lib.utils2 import safe_int
from rhodecode.lib import system_info
from rhodecode.lib import user_sessions
from rhodecode.lib import helpers as h


log = logging.getLogger(__name__)


class AdminSessionSettingsView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def settings_sessions(self):
        c = self.load_default_context()

        c.active = 'sessions'
        c.navlist = navigation_list(self.request)

        c.cleanup_older_days = 60
        older_than_seconds = 60 * 60 * 24 * c.cleanup_older_days

        config = system_info.rhodecode_config().get_value()['value']['config']
        c.session_model = user_sessions.get_session_handler(
            config.get('beaker.session.type', 'memory'))(config)

        c.session_conf = c.session_model.config
        c.session_count = c.session_model.get_count()
        c.session_expired_count = c.session_model.get_expired_count(
            older_than_seconds)

        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    def settings_sessions_cleanup(self):
        _ = self.request.translate
        expire_days = safe_int(self.request.params.get('expire_days'))

        if expire_days is None:
            expire_days = 60

        older_than_seconds = 60 * 60 * 24 * expire_days

        config = system_info.rhodecode_config().get_value()['value']['config']
        session_model = user_sessions.get_session_handler(
            config.get('beaker.session.type', 'memory'))(config)

        try:
            session_model.clean_sessions(
                older_than_seconds=older_than_seconds)
            h.flash(_('Cleaned up old sessions'), category='success')
        except user_sessions.CleanupCommand as msg:
            h.flash(msg.message, category='warning')
        except Exception as e:
            log.exception('Failed session cleanup')
            h.flash(_('Failed to cleanup up old sessions'), category='error')

        redirect_to = self.request.resource_path(
            self.context, route_name='admin_settings_sessions')
        return HTTPFound(redirect_to)
