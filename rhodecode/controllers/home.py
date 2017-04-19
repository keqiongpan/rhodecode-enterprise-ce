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

    def _get_groups_and_repos(self, repo_group_id=None):
        # repo groups groups
        repo_group_list = RepoGroup.get_all_repo_groups(group_id=repo_group_id)
        _perms = ['group.read', 'group.write', 'group.admin']
        repo_group_list_acl = RepoGroupList(repo_group_list, perm_set=_perms)
        repo_group_data = RepoGroupModel().get_repo_groups_as_dict(
            repo_group_list=repo_group_list_acl, admin=False)

        # repositories
        repo_list = Repository.get_all_repos(group_id=repo_group_id)
        _perms = ['repository.read', 'repository.write', 'repository.admin']
        repo_list_acl = RepoList(repo_list, perm_set=_perms)
        repo_data = RepoModel().get_repos_as_dict(
            repo_list=repo_list_acl, admin=False)

        return repo_data, repo_group_data

    @LoginRequired()
    def index(self):
        c.repo_group = None

        repo_data, repo_group_data = self._get_groups_and_repos()
        # json used to render the grids
        c.repos_data = json.dumps(repo_data)
        c.repo_groups_data = json.dumps(repo_group_data)

        return render('/index.mako')

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator('group.read', 'group.write',
                                        'group.admin')
    def index_repo_group(self, group_name):
        """GET /repo_group_name: Show a specific item"""
        c.repo_group = RepoGroupModel()._get_repo_group(group_name)
        repo_data, repo_group_data = self._get_groups_and_repos(
            c.repo_group.group_id)

        # json used to render the grids
        c.repos_data = json.dumps(repo_data)
        c.repo_groups_data = json.dumps(repo_group_data)

        return render('index_repo_group.mako')
