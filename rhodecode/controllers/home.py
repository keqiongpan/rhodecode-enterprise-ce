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
Home controller for RhodeCode Enterprise
"""

import logging
import time

from pylons import tmpl_context as c

from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator,
    HasRepoGroupPermissionAnyDecorator)
from rhodecode.lib.base import BaseController, render

from rhodecode.lib.ext_json import json
from rhodecode.model.db import Repository, RepoGroup
from rhodecode.model.repo import RepoModel
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.scm import RepoList, RepoGroupList


log = logging.getLogger(__name__)


class HomeController(BaseController):
    def __before__(self):
        super(HomeController, self).__before__()

    def ping(self):
        """
        Ping, doesn't require login, good for checking out the platform
        """
        instance_id = getattr(c, 'rhodecode_instanceid', '')
        return 'pong[%s] => %s' % (instance_id, self.ip_addr,)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def error_test(self):
        """
        Test exception handling and emails on errors
        """
        class TestException(Exception):
            pass

        msg = ('RhodeCode Enterprise %s test exception. Generation time: %s'
               % (c.rhodecode_name, time.time()))
        raise TestException(msg)
