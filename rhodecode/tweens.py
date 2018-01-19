# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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

from rhodecode.lib.middleware.vcs import (
    detect_vcs_request, VCS_TYPE_KEY, VCS_TYPE_SKIP)


log = logging.getLogger(__name__)


def vcs_detection_tween_factory(handler, registry):

    def vcs_detection_tween(request):
        """
        Do detection of vcs type, and save results for other layers to re-use
        this information
        """
        vcs_server_enabled = request.registry.settings.get('vcs.server.enable')
        vcs_handler = vcs_server_enabled and detect_vcs_request(
            request.environ, request.registry.settings.get('vcs.backends'))

        if vcs_handler:
            # save detected VCS type for later re-use
            request.environ[VCS_TYPE_KEY] = vcs_handler.SCM
            request.vcs_call = vcs_handler.SCM

            log.debug('Processing request with `%s` handler', handler)
            return handler(request)

        # mark that we didn't detect an VCS, and we can skip detection later on
        request.environ[VCS_TYPE_KEY] = VCS_TYPE_SKIP

        log.debug('Processing request with `%s` handler', handler)
        return handler(request)

    return vcs_detection_tween


def includeme(config):
    config.add_subscriber('rhodecode.subscribers.add_renderer_globals',
                          'pyramid.events.BeforeRender')
    config.add_subscriber('rhodecode.subscribers.set_user_lang',
                          'pyramid.events.NewRequest')
    config.add_subscriber('rhodecode.subscribers.add_localizer',
                          'pyramid.events.NewRequest')
    config.add_subscriber('rhodecode.subscribers.add_request_user_context',
                          'pyramid.events.ContextFound')

    config.add_tween('rhodecode.tweens.vcs_detection_tween_factory')
