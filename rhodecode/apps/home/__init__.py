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
from rhodecode.config import routing_links


class VCSCallPredicate(object):
    def __init__(self, val, config):
        self.val = val

    def text(self):
        return 'vcs_call route = %s' % self.val

    phash = text

    def __call__(self, info, request):
        if hasattr(request, 'vcs_call'):
            # skip vcs calls
            return False

        return True


def includeme(config):
    from rhodecode.apps.home.views import HomeView
    
    config.add_route_predicate(
        'skip_vcs_call', VCSCallPredicate)

    config.add_route(
        name='home',
        pattern='/')
    config.add_view(
        HomeView,
        attr='main_page',
        route_name='home', request_method='GET',
        renderer='rhodecode:templates/index.mako')

    config.add_route(
        name='main_page_repos_data',
        pattern='/_home_repos')
    config.add_view(
        HomeView,
        attr='main_page_repos_data',
        route_name='main_page_repos_data',
        request_method='GET', renderer='json_ext', xhr=True)

    config.add_route(
        name='main_page_repo_groups_data',
        pattern='/_home_repo_groups')
    config.add_view(
        HomeView,
        attr='main_page_repo_groups_data',
        route_name='main_page_repo_groups_data',
        request_method='GET', renderer='json_ext', xhr=True)

    config.add_route(
        name='user_autocomplete_data',
        pattern='/_users')
    config.add_view(
        HomeView,
        attr='user_autocomplete_data',
        route_name='user_autocomplete_data', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='user_group_autocomplete_data',
        pattern='/_user_groups')
    config.add_view(
        HomeView,
        attr='user_group_autocomplete_data',
        route_name='user_group_autocomplete_data', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='repo_list_data',
        pattern='/_repos')
    config.add_view(
        HomeView,
        attr='repo_list_data',
        route_name='repo_list_data', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='repo_group_list_data',
        pattern='/_repo_groups')
    config.add_view(
        HomeView,
        attr='repo_group_list_data',
        route_name='repo_group_list_data', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='goto_switcher_data',
        pattern='/_goto_data')
    config.add_view(
        HomeView,
        attr='goto_switcher_data',
        route_name='goto_switcher_data', request_method='GET',
        renderer='json_ext', xhr=True)

    config.add_route(
        name='markup_preview',
        pattern='/_markup_preview')
    config.add_view(
        HomeView,
        attr='markup_preview',
        route_name='markup_preview', request_method='POST',
        renderer='string', xhr=True)

    config.add_route(
        name='file_preview',
        pattern='/_file_preview')
    config.add_view(
        HomeView,
        attr='file_preview',
        route_name='file_preview', request_method='POST',
        renderer='string', xhr=True)

    config.add_route(
        name='store_user_session_value',
        pattern='/_store_session_attr')
    config.add_view(
        HomeView,
        attr='store_user_session_attr',
        route_name='store_user_session_value', request_method='POST',
        renderer='string', xhr=True)

    # register our static links via redirection mechanism
    routing_links.connect_redirection_links(config)

