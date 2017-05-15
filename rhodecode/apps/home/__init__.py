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
from rhodecode.config import routing_links


def includeme(config):

    config.add_route(
        name='home',
        pattern='/')

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
        name='goto_switcher_data',
        pattern='/_goto_data')

    # register our static links via redirection mechanism
    routing_links.connect_redirection_links(config)

    # Scan module for configuration decorators.
    config.scan()
