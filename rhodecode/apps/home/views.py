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

from pyramid.view import view_config

from rhodecode.apps._base import BaseAppView
from rhodecode.lib.auth import LoginRequired, NotAnonymous
from rhodecode.lib.utils2 import str2bool
from rhodecode.model.repo import RepoModel

log = logging.getLogger(__name__)


class HomeView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.user = c.auth_user.get_instance()
        self._register_global_c(c)
        return c

    @LoginRequired()
    @view_config(
        route_name='user_autocomplete_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def user_autocomplete_data(self):
        query = self.request.GET.get('query')
        active = str2bool(self.request.GET.get('active') or True)
        include_groups = str2bool(self.request.GET.get('user_groups'))

        log.debug('generating user list, query:%s, active:%s, with_groups:%s',
                  query, active, include_groups)

        repo_model = RepoModel()
        _users = repo_model.get_users(
            name_contains=query, only_active=active)

        if include_groups:
            # extend with user groups
            _user_groups = repo_model.get_user_groups(
                name_contains=query, only_active=active)
            _users = _users + _user_groups

        return {'suggestions': _users}

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='user_group_autocomplete_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def user_group_autocomplete_data(self):
        query = self.request.GET.get('query')
        active = str2bool(self.request.GET.get('active') or True)
        log.debug('generating user group list, query:%s, active:%s',
                  query, active)

        repo_model = RepoModel()
        _user_groups = repo_model.get_user_groups(
            name_contains=query, only_active=active)
        _user_groups = _user_groups

        return {'suggestions': _user_groups}
