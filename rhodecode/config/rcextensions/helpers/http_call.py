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

"""
us in hooks::

    from .helpers import http_call
    # returns response after making a POST call
    response = http_call.run(url=url, json_data={"key": "val"})

    # returns response after making a GET call
    response = http_call.run(url=url, params={"key": "val"}, method='get')

"""

from rhodecode.integrations.types.base import requests_retry_call


def run(url, json_data=None, params=None, method='post'):
    requests_session = requests_retry_call()
    requests_session.verify = True  # Verify SSL
    method_caller = getattr(requests_session, method, 'post')

    timeout = 60
    if json_data:
        resp = method_caller(url, json=json_data, timeout=timeout)
    elif params:
        resp = method_caller(url, params=params, timeout=timeout)
    else:
        raise AttributeError('Provide json_data= or params= in function call')
    resp.raise_for_status()  # raise exception on a failed request
    return resp

