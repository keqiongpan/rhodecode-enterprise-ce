# -*- coding: utf-8 -*-

# Copyright (C) 2016-2019 RhodeCode GmbH
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

import os
import hashlib
import itsdangerous
import logging
import requests
import datetime

from dogpile.core import ReadWriteMutex
from pyramid.threadlocal import get_current_registry

import rhodecode.lib.helpers as h
from rhodecode.lib.auth import HasRepoPermissionAny
from rhodecode.lib.ext_json import json
from rhodecode.model.db import User

log = logging.getLogger(__name__)

LOCK = ReadWriteMutex()

STATE_PUBLIC_KEYS = ['id', 'username', 'first_name', 'last_name',
                     'icon_link', 'display_name', 'display_link']


class ChannelstreamException(Exception):
    pass


class ChannelstreamConnectionException(ChannelstreamException):
    pass


class ChannelstreamPermissionException(ChannelstreamException):
    pass


def get_channelstream_server_url(config, endpoint):
    return 'http://{}{}'.format(config['server'], endpoint)


def channelstream_request(config, payload, endpoint, raise_exc=True):
    signer = itsdangerous.TimestampSigner(config['secret'])
    sig_for_server = signer.sign(endpoint)
    secret_headers = {'x-channelstream-secret': sig_for_server,
                      'x-channelstream-endpoint': endpoint,
                      'Content-Type': 'application/json'}
    req_url = get_channelstream_server_url(config, endpoint)
    response = None
    try:
        response = requests.post(req_url, data=json.dumps(payload),
                                 headers=secret_headers).json()
    except requests.ConnectionError:
        log.exception('ConnectionError occurred for endpoint %s', req_url)
        if raise_exc:
            raise ChannelstreamConnectionException(req_url)
    except Exception:
        log.exception('Exception related to Channelstream happened')
        if raise_exc:
            raise ChannelstreamConnectionException()
    return response


def get_user_data(user_id):
    user = User.get(user_id)
    return {
        'id': user.user_id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'icon_link': h.gravatar_url(user.email, 60),
        'display_name': h.person(user, 'username_or_name_or_email'),
        'display_link': h.link_to_user(user),
        'notifications': user.user_data.get('notification_status', True)
    }


def broadcast_validator(channel_name):
    """ checks if user can access the broadcast channel """
    if channel_name == 'broadcast':
        return True


def repo_validator(channel_name):
    """ checks if user can access the broadcast channel """
    channel_prefix = '/repo$'
    if channel_name.startswith(channel_prefix):
        elements = channel_name[len(channel_prefix):].split('$')
        repo_name = elements[0]
        can_access = HasRepoPermissionAny(
            'repository.read',
            'repository.write',
            'repository.admin')(repo_name)
        log.debug(
            'permission check for %s channel resulted in %s',
            repo_name, can_access)
        if can_access:
            return True
    return False


def check_channel_permissions(channels, plugin_validators, should_raise=True):
    valid_channels = []

    validators = [broadcast_validator, repo_validator]
    if plugin_validators:
        validators.extend(plugin_validators)
    for channel_name in channels:
        is_valid = False
        for validator in validators:
            if validator(channel_name):
                is_valid = True
                break
        if is_valid:
            valid_channels.append(channel_name)
        else:
            if should_raise:
                raise ChannelstreamPermissionException()
    return valid_channels


def get_channels_info(self, channels):
    payload = {'channels': channels}
    # gather persistence info
    return channelstream_request(self._config(), payload, '/info')


def parse_channels_info(info_result, include_channel_info=None):
    """
    Returns data that contains only secure information that can be
    presented to clients
    """
    include_channel_info = include_channel_info or []

    user_state_dict = {}
    for userinfo in info_result['users']:
        user_state_dict[userinfo['user']] = {
            k: v for k, v in userinfo['state'].items()
            if k in STATE_PUBLIC_KEYS
            }

    channels_info = {}

    for c_name, c_info in info_result['channels'].items():
        if c_name not in include_channel_info:
            continue
        connected_list = []
        for userinfo in c_info['users']:
            connected_list.append({
                'user': userinfo['user'],
                'state': user_state_dict[userinfo['user']]
            })
        channels_info[c_name] = {'users': connected_list,
                                 'history': c_info['history']}

    return channels_info


def log_filepath(history_location, channel_name):
    hasher = hashlib.sha256()
    hasher.update(channel_name.encode('utf8'))
    filename = '{}.log'.format(hasher.hexdigest())
    filepath = os.path.join(history_location, filename)
    return filepath


def read_history(history_location, channel_name):
    filepath = log_filepath(history_location, channel_name)
    if not os.path.exists(filepath):
        return []
    history_lines_limit = -100
    history = []
    with open(filepath, 'rb') as f:
        for line in f.readlines()[history_lines_limit:]:
            try:
                history.append(json.loads(line))
            except Exception:
                log.exception('Failed to load history')
    return history


def update_history_from_logs(config, channels, payload):
    history_location = config.get('history.location')
    for channel in channels:
        history = read_history(history_location, channel)
        payload['channels_info'][channel]['history'] = history


def write_history(config, message):
    """ writes a messge to a base64encoded filename """
    history_location = config.get('history.location')
    if not os.path.exists(history_location):
        return
    try:
        LOCK.acquire_write_lock()
        filepath = log_filepath(history_location, message['channel'])
        with open(filepath, 'ab') as f:
            json.dump(message, f)
            f.write('\n')
    finally:
        LOCK.release_write_lock()


def get_connection_validators(registry):
    validators = []
    for k, config in registry.rhodecode_plugins.iteritems():
        validator = config.get('channelstream', {}).get('connect_validator')
        if validator:
            validators.append(validator)
    return validators


def post_message(channel, message, username, registry=None):

    if not registry:
        registry = get_current_registry()

    log.debug('Channelstream: sending notification to channel %s', channel)
    rhodecode_plugins = getattr(registry, 'rhodecode_plugins', {})
    channelstream_config = rhodecode_plugins.get('channelstream', {})
    if channelstream_config.get('enabled'):
        payload = {
            'type': 'message',
            'timestamp': datetime.datetime.utcnow(),
            'user': 'system',
            'exclude_users': [username],
            'channel': channel,
            'message': {
                'message': message,
                'level': 'success',
                'topic': '/notifications'
            }
        }

        try:
            return channelstream_request(
                channelstream_config, [payload], '/message',
                raise_exc=False)
        except ChannelstreamException:
            log.exception('Failed to send channelstream data')
            raise
