# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 RhodeCode GmbH
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
from pylons import tmpl_context as c

from rhodecode.lib.utils2 import StrictAttributeDict

log = logging.getLogger(__name__)


class TemplateArgs(StrictAttributeDict):
    pass


class BaseAppView(object):

    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.session = request.session
        self._rhodecode_user = request.user

    def _get_local_tmpl_context(self):
        return TemplateArgs()

    def _get_template_context(self, tmpl_args):

        for k, v in tmpl_args.items():
            setattr(c, k, v)

        return {
            'defaults': {},
            'errors': {},
        }

