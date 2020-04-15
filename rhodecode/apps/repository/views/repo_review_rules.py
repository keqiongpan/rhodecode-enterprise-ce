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

from pyramid.view import view_config

from rhodecode.apps._base import RepoAppView
from rhodecode.apps.repository.utils import get_default_reviewers_data
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.model.db import Repository

log = logging.getLogger(__name__)


class RepoReviewRulesView(RepoAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @view_config(
        route_name='repo_reviewers', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def repo_review_rules(self):
        c = self.load_default_context()
        c.active = 'reviewers'

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_default_reviewers_data', request_method='GET',
        renderer='json_ext')
    def repo_default_reviewers_data(self):
        self.load_default_context()
        target_repo_name = self.request.GET.get('target_repo', self.db_repo.repo_name)
        target_repo = Repository.get_by_repo_name(target_repo_name)
        review_data = get_default_reviewers_data(
            self.db_repo.user, None, None, target_repo, None)
        return review_data
