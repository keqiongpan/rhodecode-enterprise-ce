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


ADMIN_PREFIX = '/_admin'
STATIC_FILE_PREFIX = '/_static'


class TemplateArgs(StrictAttributeDict):
    pass


class BaseAppView(object):

    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.session = request.session
        self._rhodecode_user = request.user  # auth user

    def _get_local_tmpl_context(self):
        c = TemplateArgs()
        c.auth_user = self.request.user
        return c

    def _register_global_c(self, tmpl_args):
        """
        Registers attributes to pylons global `c`
        """
        # TODO(marcink): remove once pyramid migration is finished
        for k, v in tmpl_args.items():
            setattr(c, k, v)

    def _get_template_context(self, tmpl_args):
        self._register_global_c(tmpl_args)

        local_tmpl_args = {
            'defaults': {},
            'errors': {},
        }
        local_tmpl_args.update(tmpl_args)
        return local_tmpl_args

    def load_default_context(self):
        """
        example:

        def load_default_context(self):
            c = self._get_local_tmpl_context()
            c.custom_var = 'foobar'
            self._register_global_c(c)
            return c
        """
        raise NotImplementedError('Needs implementation in view class')

