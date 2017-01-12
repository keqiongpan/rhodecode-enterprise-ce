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

from pyramid.view import view_config

from rhodecode.translation import _
from rhodecode.svn_support.utils import generate_mod_dav_svn_config

from rhodecode.admin.views.base import AdminSettingsView
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired)

log = logging.getLogger(__name__)


class SvnConfigAdminSettingsView(AdminSettingsView):

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
