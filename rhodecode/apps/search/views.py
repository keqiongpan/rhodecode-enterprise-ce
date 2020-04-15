# -*- coding: utf-8 -*-

# Copyright (C) 2011-2020 RhodeCode GmbH
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
import urllib
from pyramid.view import view_config
from webhelpers2.html.tools import update_params

from rhodecode.apps._base import BaseAppView, RepoAppView, RepoGroupAppView
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, HasRepoGroupPermissionAnyDecorator)
from rhodecode.lib.helpers import Page
from rhodecode.lib.utils2 import safe_str
from rhodecode.lib.index import searcher_from_config
from rhodecode.model import validation_schema
from rhodecode.model.validation_schema.schemas import search_schema

log = logging.getLogger(__name__)


def perform_search(request, tmpl_context, repo_name=None, repo_group_name=None):
    searcher = searcher_from_config(request.registry.settings)
    formatted_results = []
    execution_time = ''

    schema = search_schema.SearchParamsSchema()
    search_tags = []
    search_params = {}
    errors = []

    try:
        search_params = schema.deserialize(
            dict(
                search_query=request.GET.get('q'),
                search_type=request.GET.get('type'),
                search_sort=request.GET.get('sort'),
                search_max_lines=request.GET.get('max_lines'),
                page_limit=request.GET.get('page_limit'),
                requested_page=request.GET.get('page'),
             )
        )
    except validation_schema.Invalid as e:
        errors = e.children

    def url_generator(page_num):

        query_params = {
            'page': page_num,
            'q': safe_str(search_query),
            'type': safe_str(search_type),
            'max_lines': search_max_lines,
            'sort': search_sort
        }

        return '?' + urllib.urlencode(query_params)

    c = tmpl_context
    search_query = search_params.get('search_query')
    search_type = search_params.get('search_type')
    search_sort = search_params.get('search_sort')
    search_max_lines = search_params.get('search_max_lines')
    if search_params.get('search_query'):
        page_limit = search_params['page_limit']
        requested_page = search_params['requested_page']

        try:
            search_result = searcher.search(
                search_query, search_type, c.auth_user, repo_name, repo_group_name,
                requested_page=requested_page, page_limit=page_limit, sort=search_sort)

            formatted_results = Page(
                search_result['results'], page=requested_page,
                item_count=search_result['count'],
                items_per_page=page_limit, url_maker=url_generator)
        finally:
            searcher.cleanup()

        search_tags = searcher.extract_search_tags(search_query)

        if not search_result['error']:
            execution_time = '%s results (%.4f seconds)' % (
                search_result['count'],
                search_result['runtime'])
        elif not errors:
            node = schema['search_query']
            errors = [
                validation_schema.Invalid(node, search_result['error'])]

    c.perm_user = c.auth_user
    c.repo_name = repo_name
    c.repo_group_name = repo_group_name
    c.errors = errors
    c.formatted_results = formatted_results
    c.runtime = execution_time
    c.cur_query = search_query
    c.search_type = search_type
    c.searcher = searcher
    c.search_tags = search_tags

    direction, sort_field = searcher.get_sort(search_type, search_sort)
    sort_definition = searcher.sort_def(search_type, direction, sort_field)
    c.sort = ''
    c.sort_tag = None
    c.sort_tag_dir = direction
    if sort_definition:
        c.sort = '{}:{}'.format(direction, sort_field)
        c.sort_tag = sort_field


class SearchView(BaseAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    @LoginRequired()
    @view_config(
        route_name='search', request_method='GET',
        renderer='rhodecode:templates/search/search.mako')
    def search(self):
        c = self.load_default_context()
        perform_search(self.request, c)
        return self._get_template_context(c)


class SearchRepoView(RepoAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.active = 'search'
        return c

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='search_repo', request_method='GET',
        renderer='rhodecode:templates/search/search.mako')
    @view_config(
        route_name='search_repo_alt', request_method='GET',
        renderer='rhodecode:templates/search/search.mako')
    def search_repo(self):
        c = self.load_default_context()
        perform_search(self.request, c, repo_name=self.db_repo_name)
        return self._get_template_context(c)


class SearchRepoGroupView(RepoGroupAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.active = 'search'
        return c

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator(
        'group.read', 'group.write', 'group.admin')
    @view_config(
        route_name='search_repo_group', request_method='GET',
        renderer='rhodecode:templates/search/search.mako')
    def search_repo_group(self):
        c = self.load_default_context()
        perform_search(self.request, c, repo_group_name=self.db_repo_group_name)
        return self._get_template_context(c)
