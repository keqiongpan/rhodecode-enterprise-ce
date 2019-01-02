# -*- coding: utf-8 -*-

# Copyright (C) 2010-2019 RhodeCode GmbH
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


import pytest

from rhodecode.api.tests.utils import build_data, api_call, assert_ok


@pytest.mark.usefixtures("testuser_api", "app")
class TestGetMethod(object):
    def test_get_methods_no_matches(self):
        id_, params = build_data(self.apikey, 'get_method', pattern='hello')
        response = api_call(self.app, params)

        expected = []
        assert_ok(id_, expected, given=response.body)

    def test_get_methods(self):
        id_, params = build_data(self.apikey, 'get_method', pattern='*comment*')
        response = api_call(self.app, params)

        expected = ['changeset_comment', 'comment_pull_request',
                    'get_pull_request_comments', 'comment_commit']
        assert_ok(id_, expected, given=response.body)

    def test_get_methods_on_single_match(self):
        id_, params = build_data(self.apikey, 'get_method',
                                 pattern='*comment_commit*')
        response = api_call(self.app, params)

        expected = ['comment_commit',
                    {'apiuser': '<RequiredType>',
                     'comment_type': "<Optional:u'note'>",
                     'commit_id': '<RequiredType>',
                     'message': '<RequiredType>',
                     'repoid': '<RequiredType>',
                     'request': '<RequiredType>',
                     'resolves_comment_id': '<Optional:None>',
                     'status': '<Optional:None>',
                     'userid': '<Optional:<OptionalAttr:apiuser>>'}]
        assert_ok(id_, expected, given=response.body)
