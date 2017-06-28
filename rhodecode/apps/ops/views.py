# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 RhodeCode GmbH
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

from rhodecode.apps._base import BaseAppView


log = logging.getLogger(__name__)


class OpsView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.user = c.auth_user.get_instance()
        self._register_global_c(c)
        return c

    @view_config(
        route_name='ops_ping', request_method='GET',
        renderer='json_ext')
    def ops_ping(self):
        data = {
            'instance': self.request.registry.settings.get('instance_id'),
        }
        if getattr(self.request, 'user'):
            data.update({
                'caller_ip': self.request.user.ip_addr,
                'caller_name': self.request.user.username,
            })
        return {'ok': data}



