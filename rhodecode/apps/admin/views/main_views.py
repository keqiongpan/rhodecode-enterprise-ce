# -*- coding: utf-8 -*-

# Copyright (C) 2016-2018 RhodeCode GmbH
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

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from rhodecode.apps._base import BaseAppView
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (LoginRequired, HasPermissionAllDecorator)
from rhodecode.model.db import PullRequest


log = logging.getLogger(__name__)


class AdminMainView(BaseAppView):

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_home', request_method='GET')
    def admin_main(self):
        # redirect _admin to audit logs...
        raise HTTPFound(h.route_path('admin_audit_logs'))

    @LoginRequired()
    @view_config(route_name='pull_requests_global_0', request_method='GET')
    @view_config(route_name='pull_requests_global_1', request_method='GET')
    @view_config(route_name='pull_requests_global', request_method='GET')
    def pull_requests(self):
        """
        Global redirect for Pull Requests

        :param pull_request_id: id of pull requests in the system
        """

        pull_request = PullRequest.get_or_404(
            self.request.matchdict['pull_request_id'])
        pull_request_id = pull_request.pull_request_id

        repo_name = pull_request.target_repo.repo_name

        raise HTTPFound(
            h.route_path('pullrequest_show', repo_name=repo_name,
                         pull_request_id=pull_request_id))
