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

from rhodecode.apps._base import BaseAppView, DataGridAppView
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (
    LoginRequired, NotAnonymous, HasRepoGroupPermissionAnyDecorator, CSRFRequired,
    HasRepoGroupPermissionAny, AuthUser)
from rhodecode.lib.codeblocks import filenode_as_lines_tokens
from rhodecode.lib.index import searcher_from_config
from rhodecode.lib.utils2 import safe_unicode, str2bool, safe_int
from rhodecode.lib.vcs.nodes import FileNode
from rhodecode.model.db import (
    func, true, or_, case, in_filter_generator, Session,
    Repository, RepoGroup, User, UserGroup)
from rhodecode.model.repo import RepoModel
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.user import UserModel
from rhodecode.model.user_group import UserGroupModel

log = logging.getLogger(__name__)


class HomeView(BaseAppView, DataGridAppView):

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

    def _get_repo_list(self, name_contains=None, repo_type=None, repo_group_name='', limit=20):
        org_query = name_contains
        allowed_ids = self._rhodecode_user.repo_acl_ids(
            ['repository.read', 'repository.write', 'repository.admin'],
            cache=False, name_filter=name_contains) or [-1]

        query = Session().query(
                Repository.repo_name,
                Repository.repo_id,
                Repository.repo_type,
                Repository.private,
            )\
            .filter(Repository.archived.isnot(true()))\
            .filter(or_(
                # generate multiple IN to fix limitation problems
                *in_filter_generator(Repository.repo_id, allowed_ids)
            ))

        query = query.order_by(case(
            [
                (Repository.repo_name.startswith(repo_group_name), repo_group_name+'/'),
            ],
        ))
        query = query.order_by(func.length(Repository.repo_name))
        query = query.order_by(Repository.repo_name)

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

    def _get_repo_group_list(self, name_contains=None, repo_group_name='', limit=20):
        org_query = name_contains
        allowed_ids = self._rhodecode_user.repo_group_acl_ids(
            ['group.read', 'group.write', 'group.admin'],
            cache=False, name_filter=name_contains) or [-1]

        query = Session().query(
                RepoGroup.group_id,
                RepoGroup.group_name,
            )\
            .filter(or_(
                # generate multiple IN to fix limitation problems
                *in_filter_generator(RepoGroup.group_id, allowed_ids)
            ))

        query = query.order_by(case(
            [
                (RepoGroup.group_name.startswith(repo_group_name), repo_group_name+'/'),
            ],
        ))
        query = query.order_by(func.length(RepoGroup.group_name))
        query = query.order_by(RepoGroup.group_name)

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
                'text': obj.group_name,
                'type': 'repo_group',
                'repo_group_id': obj.group_id,
                'url': h.route_path(
                    'repo_group_home', repo_group_name=obj.group_name)
            }
            for obj in acl_iter]

    def _get_user_list(self, name_contains=None, limit=20):
        org_query = name_contains
        if not name_contains:
            return [], False

        # TODO(marcink): should all logged in users be allowed to search others?
        allowed_user_search = self._rhodecode_user.username != User.DEFAULT_USER
        if not allowed_user_search:
            return [], False

        name_contains = re.compile('(?:user:[ ]?)(.+)').findall(name_contains)
        if len(name_contains) != 1:
            return [], False

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
                'value_display': 'user: `{}`'.format(obj.username),
                'type': 'user',
                'icon_link': h.gravatar_url(obj.email, 30),
                'url': h.route_path(
                    'user_profile', username=obj.username)
            }
            for obj in acl_iter], True

    def _get_user_groups_list(self, name_contains=None, limit=20):
        org_query = name_contains
        if not name_contains:
            return [], False

        # TODO(marcink): should all logged in users be allowed to search others?
        allowed_user_search = self._rhodecode_user.username != User.DEFAULT_USER
        if not allowed_user_search:
            return [], False

        name_contains = re.compile('(?:user_group:[ ]?)(.+)').findall(name_contains)
        if len(name_contains) != 1:
            return [], False

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
                'value_display': 'user_group: `{}`'.format(obj.users_group_name),
                'type': 'user_group',
                'url': h.route_path(
                    'user_group_profile', user_group_name=obj.users_group_name)
            }
            for obj in acl_iter], True

    def _get_hash_commit_list(self, auth_user, searcher, query, repo=None, repo_group=None):
        repo_name = repo_group_name = None
        if repo:
            repo_name = repo.repo_name
        if repo_group:
            repo_group_name = repo_group.group_name

        org_query = query
        if not query or len(query) < 3 or not searcher:
            return [], False

        commit_hashes = re.compile('(?:commit:[ ]?)([0-9a-f]{2,40})').findall(query)

        if len(commit_hashes) != 1:
            return [], False

        commit_hash = commit_hashes[0]

        result = searcher.search(
            'commit_id:{}*'.format(commit_hash), 'commit', auth_user,
            repo_name, repo_group_name, raise_on_exc=False)

        commits = []
        for entry in result['results']:
            repo_data = {
                'repository_id': entry.get('repository_id'),
                'repository_type': entry.get('repo_type'),
                'repository_name': entry.get('repository'),
            }

            commit_entry = {
                'id': entry['commit_id'],
                'value': org_query,
                'value_display': '`{}` commit: {}'.format(
                    entry['repository'], entry['commit_id']),
                'type': 'commit',
                'repo': entry['repository'],
                'repo_data': repo_data,

                'url': h.route_path(
                    'repo_commit',
                    repo_name=entry['repository'], commit_id=entry['commit_id'])
            }

            commits.append(commit_entry)
        return commits, True

    def _get_path_list(self, auth_user, searcher, query, repo=None, repo_group=None):
        repo_name = repo_group_name = None
        if repo:
            repo_name = repo.repo_name
        if repo_group:
            repo_group_name = repo_group.group_name

        org_query = query
        if not query or len(query) < 3 or not searcher:
            return [], False

        paths_re = re.compile('(?:file:[ ]?)(.+)').findall(query)
        if len(paths_re) != 1:
            return [], False

        file_path = paths_re[0]

        search_path = searcher.escape_specials(file_path)
        result = searcher.search(
            'file.raw:*{}*'.format(search_path), 'path', auth_user,
            repo_name, repo_group_name, raise_on_exc=False)

        files = []
        for entry in result['results']:
            repo_data = {
                'repository_id': entry.get('repository_id'),
                'repository_type': entry.get('repo_type'),
                'repository_name': entry.get('repository'),
            }

            file_entry = {
                'id': entry['commit_id'],
                'value': org_query,
                'value_display': '`{}` file: {}'.format(
                    entry['repository'], entry['file']),
                'type': 'file',
                'repo': entry['repository'],
                'repo_data': repo_data,

                'url': h.route_path(
                    'repo_files',
                    repo_name=entry['repository'], commit_id=entry['commit_id'],
                    f_path=entry['file'])
            }

            files.append(file_entry)
        return files, True

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
        route_name='repo_group_list_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def repo_group_list_data(self):
        _ = self.request.translate
        self.load_default_context()

        query = self.request.GET.get('query')

        log.debug('generating repo group list, query:%s',
                  query)

        res = []
        repo_groups = self._get_repo_group_list(query)
        if repo_groups:
            res.append({
                'text': _('Repository Groups'),
                'children': repo_groups
            })

        data = {
            'more': False,
            'results': res
        }
        return data

    def _get_default_search_queries(self, search_context, searcher, query):
        if not searcher:
            return []

        is_es_6 = searcher.is_es_6

        queries = []
        repo_group_name, repo_name, repo_context = None, None, None

        # repo group context
        if search_context.get('search_context[repo_group_name]'):
            repo_group_name = search_context.get('search_context[repo_group_name]')
        if search_context.get('search_context[repo_name]'):
            repo_name = search_context.get('search_context[repo_name]')
            repo_context = search_context.get('search_context[repo_view_type]')

        if is_es_6 and repo_name:
            # files
            def query_modifier():
                qry = query
                return {'q': qry, 'type': 'content'}

            label = u'File search for `{}`'.format(h.escape(query))
            file_qry = {
                'id': -10,
                'value': query,
                'value_display': label,
                'value_icon': '<i class="icon-code"></i>',
                'type': 'search',
                'subtype': 'repo',
                'url': h.route_path('search_repo',
                                    repo_name=repo_name,
                                    _query=query_modifier())
                }

            # commits
            def query_modifier():
                qry = query
                return {'q': qry, 'type': 'commit'}

            label = u'Commit search for `{}`'.format(h.escape(query))
            commit_qry = {
                'id': -20,
                'value': query,
                'value_display': label,
                'value_icon': '<i class="icon-history"></i>',
                'type': 'search',
                'subtype': 'repo',
                'url': h.route_path('search_repo',
                                    repo_name=repo_name,
                                    _query=query_modifier())
                }

            if repo_context in ['commit', 'commits']:
                queries.extend([commit_qry, file_qry])
            elif repo_context in ['files', 'summary']:
                queries.extend([file_qry, commit_qry])
            else:
                queries.extend([commit_qry, file_qry])

        elif is_es_6 and repo_group_name:
            # files
            def query_modifier():
                qry = query
                return {'q': qry, 'type': 'content'}

            label = u'File search for `{}`'.format(query)
            file_qry = {
                'id': -30,
                'value': query,
                'value_display': label,
                'value_icon': '<i class="icon-code"></i>',
                'type': 'search',
                'subtype': 'repo_group',
                'url': h.route_path('search_repo_group',
                                    repo_group_name=repo_group_name,
                                    _query=query_modifier())
                }

            # commits
            def query_modifier():
                qry = query
                return {'q': qry, 'type': 'commit'}

            label = u'Commit search for `{}`'.format(query)
            commit_qry = {
                'id': -40,
                'value': query,
                'value_display': label,
                'value_icon': '<i class="icon-history"></i>',
                'type': 'search',
                'subtype': 'repo_group',
                'url': h.route_path('search_repo_group',
                                    repo_group_name=repo_group_name,
                                    _query=query_modifier())
                }

            if repo_context in ['commit', 'commits']:
                queries.extend([commit_qry, file_qry])
            elif repo_context in ['files', 'summary']:
                queries.extend([file_qry, commit_qry])
            else:
                queries.extend([commit_qry, file_qry])

        # Global, not scoped
        if not queries:
            queries.append(
                {
                    'id': -1,
                    'value': query,
                    'value_display': u'File search for: `{}`'.format(query),
                    'value_icon': '<i class="icon-code"></i>',
                    'type': 'search',
                    'subtype': 'global',
                    'url': h.route_path('search',
                                        _query={'q': query, 'type': 'content'})
                })
            queries.append(
                {
                    'id': -2,
                    'value': query,
                    'value_display': u'Commit search for: `{}`'.format(query),
                    'value_icon': '<i class="icon-history"></i>',
                    'type': 'search',
                    'subtype': 'global',
                    'url': h.route_path('search',
                                        _query={'q': query, 'type': 'commit'})
                })

        return queries

    @LoginRequired()
    @view_config(
        route_name='goto_switcher_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def goto_switcher_data(self):
        c = self.load_default_context()

        _ = self.request.translate

        query = self.request.GET.get('query')
        log.debug('generating main filter data, query %s', query)

        res = []
        if not query:
            return {'suggestions': res}

        def no_match(name):
            return {
                'id': -1,
                'value': "",
                'value_display': name,
                'type': 'text',
                'url': ""
            }
        searcher = searcher_from_config(self.request.registry.settings)
        has_specialized_search = False

        # set repo context
        repo = None
        repo_id = safe_int(self.request.GET.get('search_context[repo_id]'))
        if repo_id:
            repo = Repository.get(repo_id)

        # set group context
        repo_group = None
        repo_group_id = safe_int(self.request.GET.get('search_context[repo_group_id]'))
        if repo_group_id:
            repo_group = RepoGroup.get(repo_group_id)
        prefix_match = False

        # user: type search
        if not prefix_match:
            users, prefix_match = self._get_user_list(query)
            if users:
                has_specialized_search = True
                for serialized_user in users:
                    res.append(serialized_user)
            elif prefix_match:
                has_specialized_search = True
                res.append(no_match('No matching users found'))

        # user_group: type search
        if not prefix_match:
            user_groups, prefix_match = self._get_user_groups_list(query)
            if user_groups:
                has_specialized_search = True
                for serialized_user_group in user_groups:
                    res.append(serialized_user_group)
            elif prefix_match:
                has_specialized_search = True
                res.append(no_match('No matching user groups found'))

        # FTS commit: type search
        if not prefix_match:
            commits, prefix_match = self._get_hash_commit_list(
                c.auth_user, searcher, query, repo, repo_group)
            if commits:
                has_specialized_search = True
                unique_repos = collections.OrderedDict()
                for commit in commits:
                    repo_name = commit['repo']
                    unique_repos.setdefault(repo_name, []).append(commit)

                for _repo, commits in unique_repos.items():
                    for commit in commits:
                        res.append(commit)
            elif prefix_match:
                has_specialized_search = True
                res.append(no_match('No matching commits found'))

        # FTS file: type search
        if not prefix_match:
            paths, prefix_match = self._get_path_list(
                c.auth_user, searcher, query, repo, repo_group)
            if paths:
                has_specialized_search = True
                unique_repos = collections.OrderedDict()
                for path in paths:
                    repo_name = path['repo']
                    unique_repos.setdefault(repo_name, []).append(path)

                for repo, paths in unique_repos.items():
                    for path in paths:
                        res.append(path)
            elif prefix_match:
                has_specialized_search = True
                res.append(no_match('No matching files found'))

        # main suggestions
        if not has_specialized_search:
            repo_group_name = ''
            if repo_group:
                repo_group_name = repo_group.group_name

            for _q in self._get_default_search_queries(self.request.GET, searcher, query):
                res.append(_q)

            repo_groups = self._get_repo_group_list(query, repo_group_name=repo_group_name)
            for serialized_repo_group in repo_groups:
                res.append(serialized_repo_group)

            repos = self._get_repo_list(query, repo_group_name=repo_group_name)
            for serialized_repo in repos:
                res.append(serialized_repo)

            if not repos and not repo_groups:
                res.append(no_match('No matches found'))

        return {'suggestions': res}

    @LoginRequired()
    @view_config(
        route_name='home', request_method='GET',
        renderer='rhodecode:templates/index.mako')
    def main_page(self):
        c = self.load_default_context()
        c.repo_group = None
        return self._get_template_context(c)

    def _main_page_repo_groups_data(self, repo_group_id):
        column_map = {
            'name': 'group_name_hash',
            'desc': 'group_description',
            'last_change': 'updated_on',
            'owner': 'user_username',
        }
        draw, start, limit = self._extract_chunk(self.request)
        search_q, order_by, order_dir = self._extract_ordering(
            self.request, column_map=column_map)
        return RepoGroupModel().get_repo_groups_data_table(
            draw, start, limit,
            search_q, order_by, order_dir,
            self._rhodecode_user, repo_group_id)

    def _main_page_repos_data(self, repo_group_id):
        column_map = {
            'name': 'repo_name',
            'desc': 'description',
            'last_change': 'updated_on',
            'owner': 'user_username',
        }
        draw, start, limit = self._extract_chunk(self.request)
        search_q, order_by, order_dir = self._extract_ordering(
            self.request, column_map=column_map)
        return RepoModel().get_repos_data_table(
            draw, start, limit,
            search_q, order_by, order_dir,
            self._rhodecode_user, repo_group_id)

    @LoginRequired()
    @view_config(
        route_name='main_page_repo_groups_data',
        request_method='GET', renderer='json_ext', xhr=True)
    def main_page_repo_groups_data(self):
        self.load_default_context()
        repo_group_id = safe_int(self.request.GET.get('repo_group_id'))

        if repo_group_id:
            group = RepoGroup.get_or_404(repo_group_id)
            _perms = AuthUser.repo_group_read_perms
            if not HasRepoGroupPermissionAny(*_perms)(
                    group.group_name, 'user is allowed to list repo group children'):
                raise HTTPNotFound()

        return self._main_page_repo_groups_data(repo_group_id)

    @LoginRequired()
    @view_config(
        route_name='main_page_repos_data',
        request_method='GET', renderer='json_ext', xhr=True)
    def main_page_repos_data(self):
        self.load_default_context()
        repo_group_id = safe_int(self.request.GET.get('repo_group_id'))

        if repo_group_id:
            group = RepoGroup.get_or_404(repo_group_id)
            _perms = AuthUser.repo_group_read_perms
            if not HasRepoGroupPermissionAny(*_perms)(
                    group.group_name, 'user is allowed to list repo group children'):
                raise HTTPNotFound()

        return self._main_page_repos_data(repo_group_id)

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator(*AuthUser.repo_group_read_perms)
    @view_config(
        route_name='repo_group_home', request_method='GET',
        renderer='rhodecode:templates/index_repo_group.mako')
    @view_config(
        route_name='repo_group_home_slash', request_method='GET',
        renderer='rhodecode:templates/index_repo_group.mako')
    def repo_group_main_page(self):
        c = self.load_default_context()
        c.repo_group = self.request.db_repo_group
        return self._get_template_context(c)

    @LoginRequired()
    @CSRFRequired()
    @view_config(
        route_name='markup_preview', request_method='POST',
        renderer='string', xhr=True)
    def markup_preview(self):
        # Technically a CSRF token is not needed as no state changes with this
        # call. However, as this is a POST is better to have it, so automated
        # tools don't flag it as potential CSRF.
        # Post is required because the payload could be bigger than the maximum
        # allowed by GET.

        text = self.request.POST.get('text')
        renderer = self.request.POST.get('renderer') or 'rst'
        if text:
            return h.render(text, renderer=renderer, mentions=True)
        return ''

    @LoginRequired()
    @CSRFRequired()
    @view_config(
        route_name='file_preview', request_method='POST',
        renderer='string', xhr=True)
    def file_preview(self):
        # Technically a CSRF token is not needed as no state changes with this
        # call. However, as this is a POST is better to have it, so automated
        # tools don't flag it as potential CSRF.
        # Post is required because the payload could be bigger than the maximum
        # allowed by GET.

        text = self.request.POST.get('text')
        file_path = self.request.POST.get('file_path')

        renderer = h.renderer_from_filename(file_path)

        if renderer:
            return h.render(text, renderer=renderer, mentions=True)
        else:
            self.load_default_context()
            _render = self.request.get_partial_renderer(
                'rhodecode:templates/files/file_content.mako')

            lines = filenode_as_lines_tokens(FileNode(file_path, text))

            return _render('render_lines', lines)

    @LoginRequired()
    @CSRFRequired()
    @view_config(
        route_name='store_user_session_value', request_method='POST',
        renderer='string', xhr=True)
    def store_user_session_attr(self):
        key = self.request.POST.get('key')
        val = self.request.POST.get('val')

        existing_value = self.request.session.get(key)
        if existing_value != val:
            self.request.session[key] = val

        return 'stored:{}:{}'.format(key, val)
