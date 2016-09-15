# -*- coding: utf-8 -*-

# Copyright (C) 2010-2016  RhodeCode GmbH
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

from pyramid.settings import asbool

from rhodecode.config.routing import ADMIN_PREFIX
from rhodecode.lib.ext_json import json


def url_gen(request):
    urls = {
        'connect': request.route_url('channelstream_connect'),
        'subscribe': request.route_url('channelstream_subscribe'),
        'longpoll': request.registry.settings.get('channelstream.longpoll_url', ''),
        'ws': request.registry.settings.get('channelstream.ws_url', '')
    }
    return json.dumps(urls)


PLUGIN_DEFINITION = {
    'name': 'channelstream',
    'config': {
        'javascript': [],
        'css': [],
        'template_hooks': {
            'plugin_init_template': 'rhodecode:templates/channelstream/plugin_init.html'
        },
        'url_gen': url_gen,
        'static': None,
        'enabled': False,
        'server': '',
        'secret': ''
    }
}


def includeme(config):
    settings = config.registry.settings
    PLUGIN_DEFINITION['config']['enabled'] = asbool(
        settings.get('channelstream.enabled'))
    PLUGIN_DEFINITION['config']['server'] = settings.get(
        'channelstream.server', '')
    PLUGIN_DEFINITION['config']['secret'] = settings.get(
        'channelstream.secret', '')
    PLUGIN_DEFINITION['config']['history.location'] = settings.get(
        'channelstream.history.location', '')
    config.register_rhodecode_plugin(
        PLUGIN_DEFINITION['name'],
        PLUGIN_DEFINITION['config']
    )
    # create plugin history location
    history_dir = PLUGIN_DEFINITION['config']['history.location']
    if history_dir and not os.path.exists(history_dir):
        os.makedirs(history_dir, 0750)

    config.add_route(
        name='channelstream_connect',
        pattern=ADMIN_PREFIX + '/channelstream/connect')
    config.add_route(
        name='channelstream_subscribe',
        pattern=ADMIN_PREFIX + '/channelstream/subscribe')
    config.scan('rhodecode.channelstream')
