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


def includeme(config):

    # Settings
    config.add_route(
        name='edit_repo',
        pattern='/{repo_name:.*?[^/]}/settings', repo_route=True)

    config.add_route(
        name='repo_maintenance',
        pattern='/{repo_name:.*?[^/]}/maintenance', repo_route=True)

    config.add_route(
        name='repo_maintenance_execute',
        pattern='/{repo_name:.*?[^/]}/maintenance/execute', repo_route=True)

    # Strip
    config.add_route(
        name='strip',
        pattern='/{repo_name:.*?[^/]}/strip', repo_route=True)

    config.add_route(
        name='strip_check',
        pattern='/{repo_name:.*?[^/]}/strip_check', repo_route=True)

    config.add_route(
        name='strip_execute',
        pattern='/{repo_name:.*?[^/]}/strip_execute', repo_route=True)
    # Scan module for configuration decorators.
    config.scan()
