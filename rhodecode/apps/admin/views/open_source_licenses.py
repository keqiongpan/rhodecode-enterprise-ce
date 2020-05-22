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

import collections
import logging

from pyramid.view import view_config

from rhodecode.apps._base import BaseAppView
from rhodecode.apps._base.navigation import navigation_list
from rhodecode.lib.auth import (LoginRequired, HasPermissionAllDecorator)
from rhodecode.lib.utils import read_opensource_licenses

log = logging.getLogger(__name__)


class OpenSourceLicensesAdminSettingsView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_open_source', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def open_source_licenses(self):
        c = self.load_default_context()
        c.active = 'open_source'
        c.navlist = navigation_list(self.request)
        c.opensource_licenses = sorted(
            read_opensource_licenses(), key=lambda d: d["name"])
        return self._get_template_context(c)
