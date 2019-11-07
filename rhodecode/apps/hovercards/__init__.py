# -*- coding: utf-8 -*-

# Copyright (C) 2018-2019 RhodeCode GmbH
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

    config.add_route(
        name='hovercard_user',
        pattern='/_hovercard/user/{user_id}')

    config.add_route(
        name='hovercard_user_group',
        pattern='/_hovercard/user_group/{user_group_id}')

    config.add_route(
        name='hovercard_pull_request',
        pattern='/_hovercard/pull_request/{pull_request_id}')

    config.add_route(
        name='hovercard_repo_commit',
        pattern='/_hovercard/commit/{repo_name:.*?[^/]}/{commit_id}', repo_route=True)

    # Scan module for configuration decorators.
    config.scan('.views', ignore='.tests')
