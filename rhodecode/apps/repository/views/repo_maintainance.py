# -*- coding: utf-8 -*-

# Copyright (C) 2011-2018 RhodeCode GmbH
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
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib import repo_maintenance

log = logging.getLogger(__name__)


class RepoMaintenanceView(RepoAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()


        return c

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @view_config(
        route_name='edit_repo_maintenance', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def repo_maintenance(self):
        c = self.load_default_context()
        c.active = 'maintenance'
        maintenance = repo_maintenance.RepoMaintenance()
        c.executable_tasks = maintenance.get_tasks_for_repo(self.db_repo)
        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @view_config(
        route_name='edit_repo_maintenance_execute', request_method='GET',
        renderer='json', xhr=True)
    def repo_maintenance_execute(self):
        c = self.load_default_context()
        c.active = 'maintenance'
        _ = self.request.translate

        maintenance = repo_maintenance.RepoMaintenance()
        executed_types = maintenance.execute(self.db_repo)

        return executed_types
