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


def assert_and_get_main_filter_content(result):
    repos = []
    groups = []
    commits = []
    users = []
    for data_item in result:
        assert data_item['id']
        assert data_item['value']
        assert data_item['value_display']
        assert data_item['url']

        if data_item['type'] == 'search':
            display_val = data_item['value_display']
            if data_item['id'] == -1:
                assert 'File content search for:' in display_val, display_val
            elif data_item['id'] == -2:
                assert 'Commit search for:' in display_val, display_val
            else:
                assert False, 'No Proper ID returned {}'.format(data_item['id'])

        elif data_item['type'] == 'repo':
            repos.append(data_item)
        elif data_item['type'] == 'repo_group':
            groups.append(data_item)
        elif data_item['type'] == 'user':
            users.append(data_item)
        elif data_item['type'] == 'commit':
            commits.append(data_item)
        else:
            raise Exception('invalid type `%s`' % data_item['type'])

    return repos, groups, users, commits


def assert_and_get_repo_list_content(result):
    repos = []
    for data in result:
        for data_item in data['children']:
            assert data_item['id']
            assert data_item['text']
            assert data_item['url']

            if data_item['type'] == 'repo':
                repos.append(data_item)
            else:
                raise Exception('invalid type %s' % data_item['type'])

    return repos
