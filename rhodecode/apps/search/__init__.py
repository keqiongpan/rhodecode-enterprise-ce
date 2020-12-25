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
from rhodecode.apps._base import ADMIN_PREFIX


def includeme(config):
    from rhodecode.apps.search.views import (
        SearchView, SearchRepoView, SearchRepoGroupView)

    config.add_route(
        name='search',
        pattern=ADMIN_PREFIX + '/search')
    config.add_view(
        SearchView,
        attr='search',
        route_name='search', request_method='GET',
        renderer='rhodecode:templates/search/search.mako')

    config.add_route(
        name='search_repo',
        pattern='/{repo_name:.*?[^/]}/_search', repo_route=True)
    config.add_view(
        SearchRepoView,
        attr='search_repo',
        route_name='search_repo', request_method='GET',
        renderer='rhodecode:templates/search/search.mako')

    config.add_route(
        name='search_repo_alt',
        pattern='/{repo_name:.*?[^/]}/search', repo_route=True)
    config.add_view(
        SearchRepoView,
        attr='search_repo',
        route_name='search_repo_alt', request_method='GET',
        renderer='rhodecode:templates/search/search.mako')

    config.add_route(
        name='search_repo_group',
        pattern='/{repo_group_name:.*?[^/]}/_search',
        repo_group_route=True)
    config.add_view(
        SearchRepoGroupView,
        attr='search_repo_group',
        route_name='search_repo_group', request_method='GET',
        renderer='rhodecode:templates/search/search.mako')
