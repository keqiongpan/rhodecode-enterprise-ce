# -*- coding: utf-8 -*-

# Copyright (C) 2017-2020 RhodeCode GmbH
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
from pyramid.view import view_config

from rhodecode.apps._base import RepoAppView
from rhodecode.lib.helpers import SqlPage
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.utils2 import safe_int
from rhodecode.model.repo import RepoModel

log = logging.getLogger(__name__)


class AuditLogsView(RepoAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @view_config(
        route_name='edit_repo_audit_logs', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def repo_audit_logs(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.db_repo = self.db_repo

        c.active = 'audit'

        p = safe_int(self.request.GET.get('page', 1), 1)

        filter_term = self.request.GET.get('filter')
        user_log = RepoModel().get_repo_log(c.db_repo, filter_term)

        def url_generator(page_num):
            query_params = {
                'page': page_num
            }
            if filter_term:
                query_params['filter'] = filter_term
            return self.request.current_route_path(_query=query_params)

        c.audit_logs = SqlPage(
            user_log, page=p, items_per_page=10, url_maker=url_generator)
        c.filter_term = filter_term
        return self._get_template_context(c)
