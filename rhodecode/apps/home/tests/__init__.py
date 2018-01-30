# -*- coding: utf-8 -*-

# Copyright (C) 2016-2018 RhodeCode GmbH
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


def assert_and_get_content(result):
    repos = []
    groups = []
    commits = []
    for data in result:
        for data_item in data['children']:
            assert data_item['id']
            assert data_item['text']
            assert data_item['url']
            if data_item['type'] == 'repo':
                repos.append(data_item)
            elif data_item['type'] == 'group':
                groups.append(data_item)
            elif data_item['type'] == 'commit':
                commits.append(data_item)
            else:
                raise Exception('invalid type %s' % data_item['type'])

    return repos, groups, commits