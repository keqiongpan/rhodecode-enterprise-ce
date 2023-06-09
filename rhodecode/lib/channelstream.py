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

USER_STATE_PUBLIC_KEYS = [
    'id', 'username', 'first_name', 'last_name',
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

    log.debug('Sending a channelstream request to endpoint: `%s`', req_url)
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
    log.debug('Got channelstream response: %s', response)
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
            if k in USER_STATE_PUBLIC_KEYS
            }

    channels_info = {}

    for c_name, c_info in info_result['channels'].items():
        if c_name not in include_channel_info:
            continue
        connected_list = []
        for username in c_info['users']:
            connected_list.append({
                'user': username,
                'state': user_state_dict[username]
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
    for k, config in registry.rhodecode_plugins.items():
        validator = config.get('channelstream', {}).get('connect_validator')
        if validator:
            validators.append(validator)
    return validators


def get_channelstream_config(registry=None):
    if not registry:
        registry = get_current_registry()

    rhodecode_plugins = getattr(registry, 'rhodecode_plugins', {})
    channelstream_config = rhodecode_plugins.get('channelstream', {})
    return channelstream_config


def post_message(channel, message, username, registry=None):
    channelstream_config = get_channelstream_config(registry)
    if not channelstream_config.get('enabled'):
        return

    message_obj = message
    if isinstance(message, basestring):
        message_obj = {
            'message': message,
            'level': 'success',
            'topic': '/notifications'
        }

    log.debug('Channelstream: sending notification to channel %s', channel)
    payload = {
        'type': 'message',
        'timestamp': datetime.datetime.utcnow(),
        'user': 'system',
        'exclude_users': [username],
        'channel': channel,
        'message': message_obj
    }

    try:
        return channelstream_request(
            channelstream_config, [payload], '/message',
            raise_exc=False)
    except ChannelstreamException:
        log.exception('Failed to send channelstream data')
        raise


def _reload_link(label):
    return (
        '<a onclick="window.location.reload()">'
        '<strong>{}</strong>'
        '</a>'.format(label)
    )


def pr_channel(pull_request):
    repo_name = pull_request.target_repo.repo_name
    pull_request_id = pull_request.pull_request_id
    channel = '/repo${}$/pr/{}'.format(repo_name, pull_request_id)
    log.debug('Getting pull-request channelstream broadcast channel: %s', channel)
    return channel


def comment_channel(repo_name, commit_obj=None, pull_request_obj=None):
    channel = None
    if commit_obj:
        channel = u'/repo${}$/commit/{}'.format(
            repo_name, commit_obj.raw_id
        )
    elif pull_request_obj:
        channel = u'/repo${}$/pr/{}'.format(
            repo_name, pull_request_obj.pull_request_id
        )
    log.debug('Getting comment channelstream broadcast channel: %s', channel)

    return channel


def pr_update_channelstream_push(request, pr_broadcast_channel, user, msg, **kwargs):
    """
    Channel push on pull request update
    """
    if not pr_broadcast_channel:
        return

    _ = request.translate

    message = '{} {}'.format(
        msg,
        _reload_link(_(' Reload page to load changes')))

    message_obj = {
        'message': message,
        'level': 'success',
        'topic': '/notifications'
    }

    post_message(
        pr_broadcast_channel, message_obj, user.username,
        registry=request.registry)


def comment_channelstream_push(request, comment_broadcast_channel, user, msg, **kwargs):
    """
    Channelstream push on comment action, on commit, or pull-request
    """
    if not comment_broadcast_channel:
        return

    _ = request.translate

    comment_data = kwargs.pop('comment_data', {})
    user_data = kwargs.pop('user_data', {})
    comment_id = comment_data.keys()[0] if comment_data else ''

    message = '<strong>{}</strong> {} #{}'.format(
        user.username,
        msg,
        comment_id,
    )

    message_obj = {
        'message': message,
        'level': 'success',
        'topic': '/notifications'
    }

    post_message(
        comment_broadcast_channel, message_obj, user.username,
        registry=request.registry)

    message_obj = {
        'message': None,
        'user': user.username,
        'comment_id': comment_id,
        'comment_data': comment_data,
        'user_data': user_data,
        'topic': '/comment'
    }
    post_message(
        comment_broadcast_channel, message_obj, user.username,
        registry=request.registry)
