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

import rhodecode
from rhodecode.lib.base import get_ip_addr, get_access_path, get_user_agent
from rhodecode.lib.utils2 import safe_str


log = logging.getLogger(__name__)


class RequestWrapperTween(object):
    def __init__(self, handler, registry):
        self.handler = handler
        self.registry = registry

        # one-time configuration code goes here

    def __call__(self, request):
        start = time.time()
        log.debug('Starting request time measurement')
        try:
            response = self.handler(request)
        finally:
            end = time.time()
            total = end - start
            count = request.request_count()
            _ver_ = rhodecode.__version__
            log.info(
                'Req[%4s] IP: %s %s Request to %s time: %.4fs [%s], RhodeCode %s',
                count, get_ip_addr(request.environ), request.environ.get('REQUEST_METHOD'),
                safe_str(get_access_path(request.environ)), total,
                get_user_agent(request. environ), _ver_
            )

        return response


def includeme(config):
    config.add_tween(
        'rhodecode.lib.middleware.request_wrapper.RequestWrapperTween',
    )
