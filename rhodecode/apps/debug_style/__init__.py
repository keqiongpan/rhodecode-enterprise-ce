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
from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.lib.utils2 import str2bool


class DebugStylePredicate(object):
    def __init__(self, val, config):
        self.val = val

    def text(self):
        return 'debug style route = %s' % self.val

    phash = text

    def __call__(self, info, request):
        return str2bool(request.registry.settings.get('debug_style'))


def includeme(config):
    config.add_route_predicate(
        'debug_style', DebugStylePredicate)

    config.add_route(
        name='debug_style_home',
        pattern=ADMIN_PREFIX + '/debug_style',
        debug_style=True)
    config.add_route(
        name='debug_style_email',
        pattern=ADMIN_PREFIX + '/debug_style/email/{email_id}',
        debug_style=True)
    config.add_route(
        name='debug_style_email_plain_rendered',
        pattern=ADMIN_PREFIX + '/debug_style/email-rendered/{email_id}',
        debug_style=True)
    config.add_route(
        name='debug_style_template',
        pattern=ADMIN_PREFIX + '/debug_style/t/{t_path}',
        debug_style=True)

    # Scan module for configuration decorators.
    config.scan('.views', ignore='.tests')
