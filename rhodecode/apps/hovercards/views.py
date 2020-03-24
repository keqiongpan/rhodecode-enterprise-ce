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

import re
import logging
import collections

from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config

from rhodecode.apps._base import BaseAppView, RepoAppView
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (
    LoginRequired, NotAnonymous, HasRepoGroupPermissionAnyDecorator, CSRFRequired,
    HasRepoPermissionAnyDecorator)
from rhodecode.lib.codeblocks import filenode_as_lines_tokens
from rhodecode.lib.index import searcher_from_config
from rhodecode.lib.utils2 import safe_unicode, str2bool, safe_int
from rhodecode.lib.ext_json import json
from rhodecode.lib.vcs.exceptions import CommitDoesNotExistError, EmptyRepositoryError
from rhodecode.lib.vcs.nodes import FileNode
from rhodecode.model.db import (
    func, true, or_, case, in_filter_generator, Repository, RepoGroup, User, UserGroup, PullRequest)
from rhodecode.model.repo import RepoModel
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.scm import RepoGroupList, RepoList
from rhodecode.model.user import UserModel
from rhodecode.model.user_group import UserGroupModel

log = logging.getLogger(__name__)


class HoverCardsView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    @LoginRequired()
    @view_config(
        route_name='hovercard_user', request_method='GET', xhr=True,
        renderer='rhodecode:templates/hovercards/hovercard_user.mako')
    def hovercard_user(self):
        c = self.load_default_context()
        user_id = self.request.matchdict['user_id']
        c.user = User.get_or_404(user_id)
        return self._get_template_context(c)

    @LoginRequired()
    @view_config(
        route_name='hovercard_username', request_method='GET', xhr=True,
        renderer='rhodecode:templates/hovercards/hovercard_user.mako')
    def hovercard_username(self):
        c = self.load_default_context()
        username = self.request.matchdict['username']
        c.user = User.get_by_username(username)
        if not c.user:
            raise HTTPNotFound()

        return self._get_template_context(c)

    @LoginRequired()
    @view_config(
        route_name='hovercard_user_group', request_method='GET', xhr=True,
        renderer='rhodecode:templates/hovercards/hovercard_user_group.mako')
    def hovercard_user_group(self):
        c = self.load_default_context()
        user_group_id = self.request.matchdict['user_group_id']
        c.user_group = UserGroup.get_or_404(user_group_id)
        return self._get_template_context(c)

    @LoginRequired()
    @view_config(
        route_name='hovercard_pull_request', request_method='GET', xhr=True,
        renderer='rhodecode:templates/hovercards/hovercard_pull_request.mako')
    def hovercard_pull_request(self):
        c = self.load_default_context()
        c.pull_request = PullRequest.get_or_404(
            self.request.matchdict['pull_request_id'])
        perms = ['repository.read', 'repository.write', 'repository.admin']
        c.can_view_pr = h.HasRepoPermissionAny(*perms)(
            c.pull_request.target_repo.repo_name)
        return self._get_template_context(c)


class HoverCardsRepoView(RepoAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='hovercard_repo_commit', request_method='GET', xhr=True,
        renderer='rhodecode:templates/hovercards/hovercard_repo_commit.mako')
    def hovercard_repo_commit(self):
        c = self.load_default_context()
        commit_id = self.request.matchdict['commit_id']
        pre_load = ['author', 'branch', 'date', 'message']
        try:
            c.commit = self.rhodecode_vcs_repo.get_commit(
                commit_id=commit_id, pre_load=pre_load)
        except (CommitDoesNotExistError, EmptyRepositoryError):
            raise HTTPNotFound()

        return self._get_template_context(c)
