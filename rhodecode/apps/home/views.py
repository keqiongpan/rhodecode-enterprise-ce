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
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, NotAnonymous
from rhodecode.lib.utils2 import safe_unicode, str2bool
from rhodecode.model.db import func, Repository
from rhodecode.model.repo import RepoModel
from rhodecode.model.scm import ScmModel


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

    def _get_repo_list(self, name_contains=None, repo_type=None, limit=20):
        query = Repository.query()\
            .order_by(func.length(Repository.repo_name))\
            .order_by(Repository.repo_name)

        if repo_type:
            query = query.filter(Repository.repo_type == repo_type)

        if name_contains:
            ilike_expression = u'%{}%'.format(safe_unicode(name_contains))
            query = query.filter(
                Repository.repo_name.ilike(ilike_expression))
            query = query.limit(limit)

        all_repos = query.all()
        # permission checks are inside this function
        repo_iter = ScmModel().get_repos(all_repos)
        return [
            {
                'id': obj['name'],
                'text': obj['name'],
                'type': 'repo',
                'obj': obj['dbrepo'],
                'url': h.url('summary_home', repo_name=obj['name'])
            }
            for obj in repo_iter]

    @LoginRequired()
    @view_config(
        route_name='repo_list_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def repo_list_data(self):
        _ = self.request.translate

        query = self.request.GET.get('query')
        repo_type = self.request.GET.get('repo_type')
        log.debug('generating repo list, query:%s, repo_type:%s',
                  query, repo_type)

        res = []
        repos = self._get_repo_list(query, repo_type=repo_type)
        if repos:
            res.append({
                'text': _('Repositories'),
                'children': repos
            })

        data = {
            'more': False,
            'results': res
        }
        return data
