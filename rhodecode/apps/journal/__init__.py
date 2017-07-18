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


from rhodecode.apps._base import ADMIN_PREFIX


def admin_routes(config):

    config.add_route(
        name='journal', pattern='/journal')
    config.add_route(
        name='journal_rss', pattern='/journal/rss')
    config.add_route(
        name='journal_atom', pattern='/journal/atom')

    config.add_route(
        name='journal_public', pattern='/public_journal')
    config.add_route(
        name='journal_public_atom', pattern='/public_journal/atom')
    config.add_route(
        name='journal_public_atom_old', pattern='/public_journal_atom')

    config.add_route(
        name='journal_public_rss', pattern='/public_journal/rss')
    config.add_route(
        name='journal_public_rss_old', pattern='/public_journal_rss')

    config.add_route(
        name='toggle_following', pattern='/toggle_following')


def includeme(config):
    config.include(admin_routes, route_prefix=ADMIN_PREFIX)
    # Scan module for configuration decorators.
    config.scan()