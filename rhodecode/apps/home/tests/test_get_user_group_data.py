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

import json

import pytest

from rhodecode.tests import TestController
from rhodecode.tests.fixture import Fixture


fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'user_autocomplete_data': '/_users',
        'user_group_autocomplete_data': '/_user_groups'
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestUserGroupAutocompleteData(TestController):

    def test_returns_list_of_user_groups(self, user_util, xhr_header):
        self.log_user()
        user_group = user_util.create_user_group(active=True)
        user_group_name = user_group.users_group_name
        response = self.app.get(
            route_path('user_group_autocomplete_data'),
            extra_environ=xhr_header, status=200)
        result = json.loads(response.body)
        values = [suggestion['value'] for suggestion in result['suggestions']]
        assert user_group_name in values

    def test_returns_inactive_user_groups_when_active_flag_sent(
            self, user_util, xhr_header):
        self.log_user()
        user_group = user_util.create_user_group(active=False)
        user_group_name = user_group.users_group_name

        response = self.app.get(
            route_path('user_group_autocomplete_data',
                       params=dict(active='0')),
            extra_environ=xhr_header, status=200)
        result = json.loads(response.body)
        values = [suggestion['value'] for suggestion in result['suggestions']]
        assert user_group_name in values

        response = self.app.get(
            route_path('user_group_autocomplete_data',
                       params=dict(active='1')),
            extra_environ=xhr_header, status=200)
        result = json.loads(response.body)
        values = [suggestion['value'] for suggestion in result['suggestions']]
        assert user_group_name not in values

    @pytest.mark.parametrize('query, count', [
        ('hello1', 0),
        ('dev', 1),
    ])
    def test_result_is_limited_when_query_is_sent(self, user_util, xhr_header, query, count):
        self.log_user()

        user_util._test_name = 'dev-test'
        user_util.create_user_group()

        response = self.app.get(
            route_path('user_group_autocomplete_data',
                       params=dict(user_groups='true',
                                   query=query)),
            extra_environ=xhr_header, status=200)

        result = json.loads(response.body)

        assert len(result['suggestions']) == count
