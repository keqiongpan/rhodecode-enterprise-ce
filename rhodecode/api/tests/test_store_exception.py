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

from rhodecode.api.tests.utils import build_data, api_call, assert_ok, assert_error


@pytest.mark.usefixtures("testuser_api", "app")
class TestStoreException(object):

    def test_store_exception_invalid_json(self):
        id_, params = build_data(self.apikey, 'store_exception',
                                 exc_data_json='XXX,{')
        response = api_call(self.app, params)

        expected = 'Failed to parse JSON data from exc_data_json field. ' \
                   'Please make sure it contains a valid JSON.'
        assert_error(id_, expected, given=response.body)

    def test_store_exception_missing_json_params_json(self):
        id_, params = build_data(self.apikey, 'store_exception',
                                 exc_data_json='{"foo":"bar"}')
        response = api_call(self.app, params)

        expected = "Missing exc_traceback, or exc_type_name in " \
                   "exc_data_json field. Missing: 'exc_traceback'"
        assert_error(id_, expected, given=response.body)

    def test_store_exception(self):
        id_, params = build_data(
            self.apikey, 'store_exception',
            exc_data_json='{"exc_traceback": "invalid", "exc_type_name":"ValueError"}')
        response = api_call(self.app, params)
        exc_id = response.json['result']['exc_id']

        expected = {
            'exc_id': exc_id,
            'exc_url': 'http://example.com/_admin/settings/exceptions/{}'.format(exc_id)
        }
        assert_ok(id_, expected, given=response.body)
