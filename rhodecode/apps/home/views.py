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

import re
import logging
import collections

from pyramid.view import view_config

from rhodecode.apps._base import BaseAppView
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (
    LoginRequired, NotAnonymous, HasRepoGroupPermissionAnyDecorator)
from rhodecode.lib.index import searcher_from_config
from rhodecode.lib.utils2 import safe_unicode, str2bool, safe_int
from rhodecode.lib.ext_json import json
from rhodecode.model.db import (
    func, or_, in_filter_generator, Repository, RepoGroup, User, UserGroup)
from rhodecode.model.repo import RepoModel
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.scm import RepoGroupList, RepoList
from rhodecode.model.user import UserModel
from rhodecode.model.user_group import UserGroupModel

log = logging.getLogger(__name__)


class HomeView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.user = c.auth_user.get_instance()

        return c

    @LoginRequired()
    @view_config(
        route_name='user_autocomplete_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def user_autocomplete_data(self):
        self.load_default_context()
        query = self.request.GET.get('query')
        active = str2bool(self.request.GET.get('active') or True)
        include_groups = str2bool(self.request.GET.get('user_groups'))
        expand_groups = str2bool(self.request.GET.get('user_groups_expand'))
        skip_default_user = str2bool(self.request.GET.get('skip_default_user'))

        log.debug('generating user list, query:%s, active:%s, with_groups:%s',
                  query, active, include_groups)

        _users = UserModel().get_users(
            name_contains=query, only_active=active)

        def maybe_skip_default_user(usr):
            if skip_default_user and usr['username'] == UserModel.cls.DEFAULT_USER:
                return False
            return True
        _users = filter(maybe_skip_default_user, _users)

        if include_groups:
            # extend with user groups
            _user_groups = UserGroupModel().get_user_groups(
                name_contains=query, only_active=active,
                expand_groups=expand_groups)
            _users = _users + _user_groups

        return {'suggestions': _users}

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='user_group_autocomplete_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def user_group_autocomplete_data(self):
        self.load_default_context()
        query = self.request.GET.get('query')
        active = str2bool(self.request.GET.get('active') or True)
        expand_groups = str2bool(self.request.GET.get('user_groups_expand'))

        log.debug('generating user group list, query:%s, active:%s',
                  query, active)

        _user_groups = UserGroupModel().get_user_groups(
            name_contains=query, only_active=active,
            expand_groups=expand_groups)
        _user_groups = _user_groups

        return {'suggestions': _user_groups}

    def _get_repo_list(self, name_contains=None, repo_type=None, limit=20):
        org_query = name_contains
        allowed_ids = self._rhodecode_user.repo_acl_ids(
            ['repository.read', 'repository.write', 'repository.admin'],
            cache=False, name_filter=name_contains) or [-1]

        query = Repository.query()\
            .order_by(func.length(Repository.repo_name))\
            .order_by(Repository.repo_name)\
            .filter(or_(
                # generate multiple IN to fix limitation problems
                *in_filter_generator(Repository.repo_id, allowed_ids)
            ))

        if repo_type:
            query = query.filter(Repository.repo_type == repo_type)

        if name_contains:
            ilike_expression = u'%{}%'.format(safe_unicode(name_contains))
            query = query.filter(
                Repository.repo_name.ilike(ilike_expression))
            query = query.limit(limit)

        acl_iter = query

        return [
            {
                'id': obj.repo_name,
                'value': org_query,
                'value_display': obj.repo_name,
                'text': obj.repo_name,
                'type': 'repo',
                'repo_id': obj.repo_id,
                'repo_type': obj.repo_type,
                'private': obj.private,
                'url': h.route_path('repo_summary', repo_name=obj.repo_name)
            }
            for obj in acl_iter]

    def _get_repo_group_list(self, name_contains=None, limit=20):
        org_query = name_contains
        allowed_ids = self._rhodecode_user.repo_group_acl_ids(
            ['group.read', 'group.write', 'group.admin'],
            cache=False, name_filter=name_contains) or [-1]

        query = RepoGroup.query()\
            .order_by(func.length(RepoGroup.group_name))\
            .order_by(RepoGroup.group_name) \
            .filter(or_(
                # generate multiple IN to fix limitation problems
                *in_filter_generator(RepoGroup.group_id, allowed_ids)
            ))

        if name_contains:
            ilike_expression = u'%{}%'.format(safe_unicode(name_contains))
            query = query.filter(
                RepoGroup.group_name.ilike(ilike_expression))
            query = query.limit(limit)

        acl_iter = query

        return [
            {
                'id': obj.group_name,
                'value': org_query,
                'value_display': obj.group_name,
                'type': 'repo_group',
                'url': h.route_path(
                    'repo_group_home', repo_group_name=obj.group_name)
            }
            for obj in acl_iter]

    def _get_user_list(self, name_contains=None, limit=20):
        org_query = name_contains
        if not name_contains:
            return []

        name_contains = re.compile('(?:user:)(.+)').findall(name_contains)
        if len(name_contains) != 1:
            return []
        name_contains = name_contains[0]

        query = User.query()\
            .order_by(func.length(User.username))\
            .order_by(User.username) \
            .filter(User.username != User.DEFAULT_USER)

        if name_contains:
            ilike_expression = u'%{}%'.format(safe_unicode(name_contains))
            query = query.filter(
                User.username.ilike(ilike_expression))
            query = query.limit(limit)

        acl_iter = query

        return [
            {
                'id': obj.user_id,
                'value': org_query,
                'value_display': obj.username,
                'type': 'user',
                'icon_link': h.gravatar_url(obj.email, 30),
                'url': h.route_path(
                    'user_profile', username=obj.username)
            }
            for obj in acl_iter]

    def _get_user_groups_list(self, name_contains=None, limit=20):
        org_query = name_contains
        if not name_contains:
            return []

        name_contains = re.compile('(?:user_group:)(.+)').findall(name_contains)
        if len(name_contains) != 1:
            return []
        name_contains = name_contains[0]

        query = UserGroup.query()\
            .order_by(func.length(UserGroup.users_group_name))\
            .order_by(UserGroup.users_group_name)

        if name_contains:
            ilike_expression = u'%{}%'.format(safe_unicode(name_contains))
            query = query.filter(
                UserGroup.users_group_name.ilike(ilike_expression))
            query = query.limit(limit)

        acl_iter = query

        return [
            {
                'id': obj.users_group_id,
                'value': org_query,
                'value_display': obj.users_group_name,
                'type': 'user_group',
                'url': h.route_path(
                    'user_group_profile', user_group_name=obj.users_group_name)
            }
            for obj in acl_iter]

    def _get_hash_commit_list(self, auth_user, query):
        org_query = query
        if not query or len(query) < 3:
            return []

        commit_hashes = re.compile('(?:commit:)([0-9a-f]{2,40})').findall(query)

        if len(commit_hashes) != 1:
            return []
        commit_hash = commit_hashes[0]

        searcher = searcher_from_config(self.request.registry.settings)
        result = searcher.search(
            'commit_id:%s*' % commit_hash, 'commit', auth_user,
            raise_on_exc=False)

        return [
            {
                'id': entry['commit_id'],
                'value': org_query,
                'value_display': 'repo `{}` commit: {}'.format(
                    entry['repository'], entry['commit_id']),
                'type': 'commit',
                'repo': entry['repository'],
                'url': h.route_path(
                    'repo_commit',
                    repo_name=entry['repository'], commit_id=entry['commit_id'])
            }
            for entry in result['results']]

    @LoginRequired()
    @view_config(
        route_name='repo_list_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def repo_list_data(self):
        _ = self.request.translate
        self.load_default_context()

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
        log.debug('generating main filter data, query %s', query)

        default_search_val = u'Full text search for: `{}`'.format(query)
        res = []
        if not query:
            return {'suggestions': res}

        res.append({
            'id': -1,
            'value': query,
            'value_display': default_search_val,
            'type': 'search',
            'url': h.route_path(
                'search', _query={'q': query})
        })
        repo_group_id = safe_int(self.request.GET.get('repo_group_id'))
        if repo_group_id:
            repo_group = RepoGroup.get(repo_group_id)
            composed_hint = '{}/{}'.format(repo_group.group_name, query)
            show_hint = not query.startswith(repo_group.group_name)
            if repo_group and show_hint:
                hint = u'Group search: `{}`'.format(composed_hint)
                res.append({
                    'id': -1,
                    'value': composed_hint,
                    'value_display': hint,
                    'type': 'hint',
                    'url': ""
                })

        repo_groups = self._get_repo_group_list(query)
        for serialized_repo_group in repo_groups:
            res.append(serialized_repo_group)

        repos = self._get_repo_list(query)
        for serialized_repo in repos:
            res.append(serialized_repo)

        # TODO(marcink): permissions for that ?
        allowed_user_search = self._rhodecode_user.username != User.DEFAULT_USER
        if allowed_user_search:
            users = self._get_user_list(query)
            for serialized_user in users:
                res.append(serialized_user)

            user_groups = self._get_user_groups_list(query)
            for serialized_user_group in user_groups:
                res.append(serialized_user_group)

        commits = self._get_hash_commit_list(c.auth_user, query)
        if commits:
            unique_repos = collections.OrderedDict()
            for commit in commits:
                repo_name = commit['repo']
                unique_repos.setdefault(repo_name, []).append(commit)

            for repo, commits in unique_repos.items():
                for commit in commits:
                    res.append(commit)

        return {'suggestions': res}

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
    @view_config(
        route_name='home', request_method='GET',
        renderer='rhodecode:templates/index.mako')
    def main_page(self):
        c = self.load_default_context()
        c.repo_group = None

        repo_data, repo_group_data = self._get_groups_and_repos()
        # json used to render the grids
        c.repos_data = json.dumps(repo_data)
        c.repo_groups_data = json.dumps(repo_group_data)

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator(
        'group.read', 'group.write', 'group.admin')
    @view_config(
        route_name='repo_group_home', request_method='GET',
        renderer='rhodecode:templates/index_repo_group.mako')
    @view_config(
        route_name='repo_group_home_slash', request_method='GET',
        renderer='rhodecode:templates/index_repo_group.mako')
    def repo_group_main_page(self):
        c = self.load_default_context()
        c.repo_group = self.request.db_repo_group
        repo_data, repo_group_data = self._get_groups_and_repos(
            c.repo_group.group_id)

        # json used to render the grids
        c.repos_data = json.dumps(repo_data)
        c.repo_groups_data = json.dumps(repo_group_data)

        return self._get_template_context(c)
