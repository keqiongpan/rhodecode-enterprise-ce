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

import time
import logging


from pyramid.httpexceptions import HTTPFound

from rhodecode.apps._base import BaseAppView
from rhodecode.lib import helpers as h

log = logging.getLogger(__name__)


class OpsView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.user = c.auth_user.get_instance()

        return c

    def ops_ping(self):
        data = {
            'instance': self.request.registry.settings.get('instance_id'),
        }
        if getattr(self.request, 'user'):
            caller_name = 'anonymous'
            if self.request.user.user_id:
                caller_name = self.request.user.username

            data.update({
                'caller_ip': self.request.user.ip_addr,
                'caller_name': caller_name,
            })
        return {'ok': data}

    def ops_error_test(self):
        """
        Test exception handling and emails on errors
        """

        class TestException(Exception):
            pass
        # add timeout so we add some sort of rate limiter
        time.sleep(2)
        msg = ('RhodeCode Enterprise test exception. '
               'Client:{}. Generation time: {}.'.format(self.request.user, time.time()))
        raise TestException(msg)

    def ops_redirect_test(self):
        """
        Test redirect handling
        """
        redirect_to = self.request.GET.get('to') or h.route_path('home')
        raise HTTPFound(redirect_to)

    def ops_healthcheck(self):
        from rhodecode.lib.system_info import load_system_info

        vcsserver_info = load_system_info('vcs_server')
        if vcsserver_info:
            vcsserver_info = vcsserver_info['human_value']

        db_info = load_system_info('database_info')
        if db_info:
            db_info = db_info['human_value']

        health_spec = {
            'caller_ip': self.request.user.ip_addr,
            'vcsserver': vcsserver_info,
            'db': db_info,
        }

        return {'healthcheck': health_spec}

