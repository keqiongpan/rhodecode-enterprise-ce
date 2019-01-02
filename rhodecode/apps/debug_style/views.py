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
import logging

from pyramid.view import view_config
from pyramid.renderers import render_to_response
from rhodecode.apps._base import BaseAppView

log = logging.getLogger(__name__)


class DebugStyleView(BaseAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()

        return c

    @view_config(
        route_name='debug_style_home', request_method='GET',
        renderer=None)
    def index(self):
        c = self.load_default_context()
        c.active = 'index'

        return render_to_response(
            'debug_style/index.html', self._get_template_context(c),
            request=self.request)

    @view_config(
        route_name='debug_style_template', request_method='GET',
        renderer=None)
    def template(self):
        t_path = self.request.matchdict['t_path']
        c = self.load_default_context()
        c.active = os.path.splitext(t_path)[0]
        c.came_from = ''

        return render_to_response(
            'debug_style/' + t_path, self._get_template_context(c),
            request=self.request)