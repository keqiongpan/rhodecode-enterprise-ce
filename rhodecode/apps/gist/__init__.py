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


def admin_routes(config):
    from rhodecode.apps.gist.views import GistView

    config.add_route(
        name='gists_show', pattern='/gists')
    config.add_view(
        GistView,
        attr='gist_show_all',
        route_name='gists_show', request_method='GET',
        renderer='rhodecode:templates/admin/gists/gist_index.mako')

    config.add_route(
        name='gists_new', pattern='/gists/new')
    config.add_view(
        GistView,
        attr='gist_new',
        route_name='gists_new', request_method='GET',
        renderer='rhodecode:templates/admin/gists/gist_new.mako')

    config.add_route(
        name='gists_create', pattern='/gists/create')
    config.add_view(
        GistView,
        attr='gist_create',
        route_name='gists_create', request_method='POST',
        renderer='rhodecode:templates/admin/gists/gist_new.mako')

    config.add_route(
        name='gist_show', pattern='/gists/{gist_id}')
    config.add_view(
        GistView,
        attr='gist_show',
        route_name='gist_show', request_method='GET',
        renderer='rhodecode:templates/admin/gists/gist_show.mako')

    config.add_route(
        name='gist_show_rev',
        pattern='/gists/{gist_id}/rev/{revision}')

    config.add_view(
        GistView,
        attr='gist_show',
        route_name='gist_show_rev', request_method='GET',
        renderer='rhodecode:templates/admin/gists/gist_show.mako')

    config.add_route(
        name='gist_show_formatted',
        pattern='/gists/{gist_id}/rev/{revision}/{format}')
    config.add_view(
        GistView,
        attr='gist_show',
        route_name='gist_show_formatted', request_method='GET',
        renderer=None)

    config.add_route(
        name='gist_show_formatted_path',
        pattern='/gists/{gist_id}/rev/{revision}/{format}/{f_path:.*}')
    config.add_view(
        GistView,
        attr='gist_show',
        route_name='gist_show_formatted_path', request_method='GET',
        renderer=None)

    config.add_route(
        name='gist_delete', pattern='/gists/{gist_id}/delete')
    config.add_view(
        GistView,
        attr='gist_delete',
        route_name='gist_delete', request_method='POST')

    config.add_route(
        name='gist_edit', pattern='/gists/{gist_id}/edit')
    config.add_view(
        GistView,
        attr='gist_edit',
        route_name='gist_edit', request_method='GET',
        renderer='rhodecode:templates/admin/gists/gist_edit.mako')

    config.add_route(
        name='gist_update', pattern='/gists/{gist_id}/update')
    config.add_view(
        GistView,
        attr='gist_update',
        route_name='gist_update', request_method='POST',
        renderer='rhodecode:templates/admin/gists/gist_edit.mako')

    config.add_route(
        name='gist_edit_check_revision',
        pattern='/gists/{gist_id}/edit/check_revision')
    config.add_view(
        GistView,
        attr='gist_edit_check_revision',
        route_name='gist_edit_check_revision', request_method='GET',
        renderer='json_ext')


def includeme(config):
    config.include(admin_routes, route_prefix=ADMIN_PREFIX)
