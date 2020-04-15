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
import datetime

from zope.cachedescriptors.property import Lazy as LazyProperty
from pyramid.threadlocal import get_current_request

from rhodecode.lib.utils2 import AttributeDict


# this is a user object to be used for events caused by the system (eg. shell)
SYSTEM_USER = AttributeDict(dict(
    username='__SYSTEM__',
    user_id='__SYSTEM_ID__'
))

log = logging.getLogger(__name__)


class RhodecodeEvent(object):
    """
    Base event class for all RhodeCode events
    """
    name = "RhodeCodeEvent"
    no_url_set = '<no server_url available>'

    def __init__(self, request=None):
        self._request = request
        self.utc_timestamp = datetime.datetime.utcnow()

    def get_request(self):
        if self._request:
            return self._request
        return get_current_request()

    @LazyProperty
    def request(self):
        return self.get_request()

    @property
    def auth_user(self):
        if not self.request:
            return

        user = getattr(self.request, 'user', None)
        if user:
            return user

        api_user = getattr(self.request, 'rpc_user', None)
        if api_user:
            return api_user

    @property
    def actor(self):
        auth_user = self.auth_user
        if auth_user:
            instance = auth_user.get_instance()
            if not instance:
                return AttributeDict(dict(
                    username=auth_user.username,
                    user_id=auth_user.user_id,
                ))
            return instance

        return SYSTEM_USER

    @property
    def actor_ip(self):
        auth_user = self.auth_user
        if auth_user:
            return auth_user.ip_addr
        return '<no ip available>'

    @property
    def server_url(self):
        if self.request:
            try:
                return self.request.route_url('home')
            except Exception:
                log.exception('Failed to fetch URL for server')
                return self.no_url_set

        return self.no_url_set

    def as_dict(self):
        data = {
            'name': self.name,
            'utc_timestamp': self.utc_timestamp,
            'actor_ip': self.actor_ip,
            'actor': {
                'username': self.actor.username,
                'user_id': self.actor.user_id
            },
            'server_url': self.server_url
        }
        return data


class RhodeCodeIntegrationEvent(RhodecodeEvent):
    """
    Special subclass for Integration events
    """
