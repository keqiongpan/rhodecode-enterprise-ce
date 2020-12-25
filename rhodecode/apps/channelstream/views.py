# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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
import uuid


from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden, HTTPBadGateway

from rhodecode.apps._base import BaseAppView
from rhodecode.lib.channelstream import (
    channelstream_request, get_channelstream_server_url,
    ChannelstreamConnectionException,
    ChannelstreamPermissionException,
    check_channel_permissions,
    get_connection_validators,
    get_user_data,
    parse_channels_info,
    update_history_from_logs,
    USER_STATE_PUBLIC_KEYS)

from rhodecode.lib.auth import NotAnonymous

log = logging.getLogger(__name__)


class ChannelstreamView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        self.channelstream_config = \
            self.request.registry.rhodecode_plugins['channelstream']
        if not self.channelstream_config.get('enabled'):
            log.error('Channelstream plugin is disabled')
            raise HTTPBadRequest()

        return c

    @NotAnonymous()
    def channelstream_connect(self):
        """ handle authorization of users trying to connect """

        self.load_default_context()
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

        user = self._rhodecode_user
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

        #user_data['permissions'] = self._rhodecode_user.permissions_safe

        payload = {
            'username': user.username,
            'user_state': user_data,
            'conn_id': str(uuid.uuid4()),
            'channels': channels,
            'channel_configs': {},
            'state_public_keys': USER_STATE_PUBLIC_KEYS,
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
        channelstream_url = get_channelstream_server_url(
            self.channelstream_config, '/connect')
        try:
            connect_result = channelstream_request(
                self.channelstream_config, payload, '/connect')
        except ChannelstreamConnectionException:
            log.exception(
                'Channelstream service at {} is down'.format(channelstream_url))
            return HTTPBadGateway()

        channel_info = connect_result.get('channels_info')
        if not channel_info:
            raise HTTPBadRequest()

        connect_result['channels'] = channels
        connect_result['channels_info'] = parse_channels_info(
            channel_info, include_channel_info=filtered_channels)
        update_history_from_logs(self.channelstream_config,
                                 filtered_channels, connect_result)
        return connect_result

    @NotAnonymous()
    def channelstream_subscribe(self):
        """ can be used to subscribe specific connection to other channels """
        self.load_default_context()
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

        channelstream_url = get_channelstream_server_url(
            self.channelstream_config, '/subscribe')
        try:
            connect_result = channelstream_request(
                self.channelstream_config, payload, '/subscribe')
        except ChannelstreamConnectionException:
            log.exception(
                'Channelstream service at {} is down'.format(channelstream_url))
            return HTTPBadGateway()

        channel_info = connect_result.get('channels_info')
        if not channel_info:
            raise HTTPBadRequest()

        # include_channel_info will limit history only to new channel
        # to not overwrite histories on other channels in client
        connect_result['channels_info'] = parse_channels_info(
            channel_info,
            include_channel_info=filtered_channels)
        update_history_from_logs(
            self.channelstream_config, filtered_channels, connect_result)
        return connect_result
