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

    config.add_route(
        name='home',
        pattern='/')

    config.add_route(
        name='main_page_repos_data',
        pattern='/_home_repos')

    config.add_route(
        name='main_page_repo_groups_data',
        pattern='/_home_repo_groups')

    config.add_route(
        name='user_autocomplete_data',
        pattern='/_users')

    config.add_route(
        name='user_group_autocomplete_data',
        pattern='/_user_groups')

    config.add_route(
        name='repo_list_data',
        pattern='/_repos')

    config.add_route(
        name='repo_group_list_data',
        pattern='/_repo_groups')

    config.add_route(
        name='goto_switcher_data',
        pattern='/_goto_data')

    config.add_route(
        name='markup_preview',
        pattern='/_markup_preview')

    config.add_route(
        name='file_preview',
        pattern='/_file_preview')

    config.add_route(
        name='store_user_session_value',
        pattern='/_store_session_attr')

    # register our static links via redirection mechanism
    routing_links.connect_redirection_links(config)

    # Scan module for configuration decorators.
    config.scan('.views', ignore='.tests')

    config.add_route_predicate(
        'skip_vcs_call', VCSCallPredicate)
