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

import re
import logging

from pyramid.view import view_config

from rhodecode.apps._base import BaseAppView
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, NotAnonymous
from rhodecode.lib.index import searcher_from_config
from rhodecode.lib.utils2 import safe_unicode, str2bool
from rhodecode.model.db import func, Repository, RepoGroup
from rhodecode.model.repo import RepoModel
from rhodecode.model.scm import ScmModel
from rhodecode.model.user import UserModel
from rhodecode.model.user_group import UserGroupModel

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

        _users = UserModel().get_users(
            name_contains=query, only_active=active)

        if include_groups:
            # extend with user groups
            _user_groups = UserGroupModel().get_user_groups(
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

        _user_groups = UserGroupModel().get_user_groups(
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

    def _get_repo_group_list(self, name_contains=None, limit=20):
        query = RepoGroup.query()\
            .order_by(func.length(RepoGroup.group_name))\
            .order_by(RepoGroup.group_name)

        if name_contains:
            ilike_expression = u'%{}%'.format(safe_unicode(name_contains))
            query = query.filter(
                RepoGroup.group_name.ilike(ilike_expression))
            query = query.limit(limit)

        all_groups = query.all()
        repo_groups_iter = ScmModel().get_repo_groups(all_groups)
        return [
            {
                'id': obj.group_name,
                'text': obj.group_name,
                'type': 'group',
                'obj': {},
                'url': h.url('repo_group_home', group_name=obj.group_name)
            }
            for obj in repo_groups_iter]

    def _get_hash_commit_list(self, auth_user, hash_starts_with=None):
        if not hash_starts_with or len(hash_starts_with) < 3:
            return []

        commit_hashes = re.compile('([0-9a-f]{2,40})').findall(hash_starts_with)

        if len(commit_hashes) != 1:
            return []

        commit_hash_prefix = commit_hashes[0]

        searcher = searcher_from_config(self.request.registry.settings)
        result = searcher.search(
            'commit_id:%s*' % commit_hash_prefix, 'commit', auth_user,
            raise_on_exc=False)

        return [
            {
                'id': entry['commit_id'],
                'text': entry['commit_id'],
                'type': 'commit',
                'obj': {'repo': entry['repository']},
                'url': h.url('changeset_home',
                             repo_name=entry['repository'],
                             revision=entry['commit_id'])
            }
            for entry in result['results']]

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

    @LoginRequired()
    @view_config(
        route_name='goto_switcher_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def goto_switcher_data(self):
        c = self.load_default_context()

        _ = self.request.translate

        query = self.request.GET.get('query')
        log.debug('generating goto switcher list, query %s', query)

        res = []
        repo_groups = self._get_repo_group_list(query)
        if repo_groups:
            res.append({
                'text': _('Groups'),
                'children': repo_groups
            })

        repos = self._get_repo_list(query)
        if repos:
            res.append({
                'text': _('Repositories'),
                'children': repos
            })

        commits = self._get_hash_commit_list(c.auth_user, query)
        if commits:
            unique_repos = {}
            for commit in commits:
                unique_repos.setdefault(commit['obj']['repo'], []
                    ).append(commit)

            for repo in unique_repos:
                res.append({
                    'text': _('Commits in %(repo)s') % {'repo': repo},
                    'children': unique_repos[repo]
                })

        data = {
            'more': False,
            'results': res
        }
        return data
