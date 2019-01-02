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
from rhodecode.apps._base import ADMIN_PREFIX


def admin_routes(config):
    config.add_route(
        name='gists_show', pattern='/gists')
    config.add_route(
        name='gists_new', pattern='/gists/new')
    config.add_route(
        name='gists_create', pattern='/gists/create')

    config.add_route(
        name='gist_show', pattern='/gists/{gist_id}')

    config.add_route(
        name='gist_delete', pattern='/gists/{gist_id}/delete')

    config.add_route(
        name='gist_edit', pattern='/gists/{gist_id}/edit')

    config.add_route(
        name='gist_edit_check_revision',
        pattern='/gists/{gist_id}/edit/check_revision')

    config.add_route(
        name='gist_update', pattern='/gists/{gist_id}/update')

    config.add_route(
        name='gist_show_rev',
        pattern='/gists/{gist_id}/{revision}')
    config.add_route(
        name='gist_show_formatted',
        pattern='/gists/{gist_id}/{revision}/{format}')

    config.add_route(
        name='gist_show_formatted_path',
        pattern='/gists/{gist_id}/{revision}/{format}/{f_path:.*}')


def includeme(config):
    config.include(admin_routes, route_prefix=ADMIN_PREFIX)
    # Scan module for configuration decorators.
    config.scan('.views', ignore='.tests')
