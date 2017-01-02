# -*- coding: utf-8 -*-

# Copyright (C) 2010-2017 RhodeCode GmbH
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
Channel Stream controller for rhodecode

:created_on: Oct 10, 2015
:author: marcinl
:copyright: (c) 2013-2015 RhodeCode GmbH.
:license: Commercial License, see LICENSE for more details.
"""

import logging
import uuid

from pylons import tmpl_context as c
from pyramid.settings import asbool
from pyramid.view import view_config
from webob.exc import HTTPBadRequest, HTTPForbidden, HTTPBadGateway

from rhodecode.lib.channelstream import (
    channelstream_request,
    ChannelstreamConnectionException,
    ChannelstreamPermissionException,
    check_channel_permissions,
    get_connection_validators,
    get_user_data,
    parse_channels_info,
    update_history_from_logs,
    STATE_PUBLIC_KEYS)
from rhodecode.lib.auth import NotAnonymous
from rhodecode.lib.utils2 import str2bool

log = logging.getLogger(__name__)


class ChannelstreamView(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

        # Some of the decorators rely on this attribute to be present
        # on the class of the decorated method.
        self._rhodecode_user = request.user
        registry = request.registry
        self.channelstream_config = registry.rhodecode_plugins['channelstream']
        if not self.channelstream_config.get('enabled'):
            log.exception('Channelstream plugin is disabled')
            raise HTTPBadRequest()

    @NotAnonymous()
    @view_config(route_name='channelstream_connect', renderer='json')
    def connect(self):
        """ handle authorization of users trying to connect """
        try:
            json_body = self.request.json_body
        except Exception:
            log.exception('Failed to decode json from request')
            raise HTTPBadRequest()
        try:
            channels = check_channel_permissions(
                json_body.get('channels'),
                get_connection_validators(self.request.registry))
        except ChannelstreamPermissionException:
            log.error('Incorrect permissions for requested channels')
            raise HTTPForbidden()

        user = c.rhodecode_user
        if user.user_id:
            user_data = get_user_data(user.user_id)
        else:
            user_data = {
                'id': None,
                'username': None,
                'first_name': None,
                'last_name': None,
                'icon_link': None,
                'display_name': None,
                'display_link': None,
            }
        user_data['permissions'] = c.rhodecode_user.permissions
        payload = {
            'username': user.username,
            'user_state': user_data,
            'conn_id': str(uuid.uuid4()),
            'channels': channels,
            'channel_configs': {},
            'state_public_keys': STATE_PUBLIC_KEYS,
            'info': {
                'exclude_channels': ['broadcast']
            }
        }
        filtered_channels = [channel for channel in channels
                             if channel != 'broadcast']
        for channel in filtered_channels:
            payload['channel_configs'][channel] = {
                'notify_presence': True,
                'history_size': 100,
                'store_history': True,
                'broadcast_presence_with_user_lists': True
            }
        # connect user to server
        try:
            connect_result = channelstream_request(self.channelstream_config,
                                                   payload, '/connect')
        except ChannelstreamConnectionException:
            log.exception('Channelstream service is down')
            return HTTPBadGateway()

        connect_result['channels'] = channels
        connect_result['channels_info'] = parse_channels_info(
            connect_result['channels_info'],
            include_channel_info=filtered_channels)
        update_history_from_logs(self.channelstream_config,
                                 filtered_channels, connect_result)
        return connect_result

    @NotAnonymous()
    @view_config(route_name='channelstream_subscribe', renderer='json')
    def subscribe(self):
        """ can be used to subscribe specific connection to other channels """
        try:
            json_body = self.request.json_body
        except Exception:
            log.exception('Failed to decode json from request')
            raise HTTPBadRequest()
        try:
            channels = check_channel_permissions(
                json_body.get('channels'),
                get_connection_validators(self.request.registry))
        except ChannelstreamPermissionException:
            log.error('Incorrect permissions for requested channels')
            raise HTTPForbidden()
        payload = {'conn_id': json_body.get('conn_id', ''),
                   'channels': channels,
                   'channel_configs': {},
                   'info': {
                       'exclude_channels': ['broadcast']}
                   }
        filtered_channels = [chan for chan in channels if chan != 'broadcast']
        for channel in filtered_channels:
            payload['channel_configs'][channel] = {
                'notify_presence': True,
                'history_size': 100,
                'store_history': True,
                'broadcast_presence_with_user_lists': True
            }
        try:
            connect_result = channelstream_request(
                self.channelstream_config, payload, '/subscribe')
        except ChannelstreamConnectionException:
            log.exception('Channelstream service is down')
            return HTTPBadGateway()
        # include_channel_info will limit history only to new channel
        # to not overwrite histories on other channels in client
        connect_result['channels_info'] = parse_channels_info(
            connect_result['channels_info'],
            include_channel_info=filtered_channels)
        update_history_from_logs(self.channelstream_config,
                                 filtered_channels, connect_result)
        return connect_result
