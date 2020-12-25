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

import logging

from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from rhodecode.apps._base import BaseAppView
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (LoginRequired, NotAnonymous, HasRepoPermissionAny)
from rhodecode.model.db import PullRequest


log = logging.getLogger(__name__)


class AdminMainView(BaseAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    @LoginRequired()
    @NotAnonymous()
    def admin_main(self):
        c = self.load_default_context()
        c.active = 'admin'

        if not (c.is_super_admin or c.is_delegated_admin):
            raise HTTPNotFound()

        return self._get_template_context(c)

    @LoginRequired()
    def pull_requests(self):
        """
        Global redirect for Pull Requests
        pull_request_id: id of pull requests in the system
        """

        pull_request = PullRequest.get_or_404(
            self.request.matchdict['pull_request_id'])
        pull_request_id = pull_request.pull_request_id

        repo_name = pull_request.target_repo.repo_name
        # NOTE(marcink):
        # check permissions so we don't redirect to repo that we don't have access to
        # exposing it's name
        target_repo_perm = HasRepoPermissionAny(
            'repository.read', 'repository.write', 'repository.admin')(repo_name)
        if not target_repo_perm:
            raise HTTPNotFound()

        raise HTTPFound(
            h.route_path('pullrequest_show', repo_name=repo_name,
                         pull_request_id=pull_request_id))
