# -*- coding: utf-8 -*-

# Copyright (C) 2010-2017  RhodeCode GmbH
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

import mock
import pytest

from rhodecode.model.db import Gist
from rhodecode.model.gist import GistModel
from rhodecode.api.tests.utils import (
    build_data, api_call, assert_error, assert_ok, crash)
from rhodecode.tests.fixture import Fixture


@pytest.mark.usefixtures("testuser_api", "app")
class TestApiCreateGist(object):
    @pytest.mark.parametrize("lifetime, gist_type, gist_acl_level", [
        (10, Gist.GIST_PUBLIC, Gist.ACL_LEVEL_PUBLIC),
        (20, Gist.GIST_PUBLIC, Gist.ACL_LEVEL_PRIVATE),
        (40, Gist.GIST_PRIVATE, Gist.ACL_LEVEL_PUBLIC),
        (80, Gist.GIST_PRIVATE, Gist.ACL_LEVEL_PRIVATE),
    ])
    def test_api_create_gist(self, lifetime, gist_type, gist_acl_level):
        id_, params = build_data(
            self.apikey_regular, 'create_gist',
            lifetime=lifetime,
            description='foobar-gist',
            gist_type=gist_type,
            acl_level=gist_acl_level,
            files={'foobar_ąć': {'content': 'foo'}})
        response = api_call(self.app, params)
        response_json = response.json
        gist = response_json['result']['gist']
        expected = {
            'gist': {
                'access_id': gist['access_id'],
                'created_on': gist['created_on'],
                'modified_at': gist['modified_at'],
                'description': 'foobar-gist',
                'expires': gist['expires'],
                'gist_id': gist['gist_id'],
                'type': gist_type,
                'url': gist['url'],
                # content is empty since we don't show it here
                'content': None,
                'acl_level': gist_acl_level,
            },
            'msg': 'created new gist'
        }
        try:
            assert_ok(id_, expected, given=response.body)
        finally:
            Fixture().destroy_gists()

    @pytest.mark.parametrize("expected, lifetime, gist_type, gist_acl_level, files", [
        ({'gist_type': '"ups" is not one of private, public'},
         10, 'ups', Gist.ACL_LEVEL_PUBLIC, {'f': {'content': 'f'}}),

        ({'lifetime': '-120 is less than minimum value -1'},
         -120, Gist.GIST_PUBLIC, Gist.ACL_LEVEL_PUBLIC, {'f': {'content': 'f'}}),

        ({'0.content': 'Required'},
         10, Gist.GIST_PUBLIC, Gist.ACL_LEVEL_PUBLIC, {'f': {'x': 'f'}}),
    ])
    def test_api_try_create_gist(
            self, expected, lifetime, gist_type, gist_acl_level, files):
        id_, params = build_data(
            self.apikey_regular, 'create_gist',
            lifetime=lifetime,
            description='foobar-gist',
            gist_type=gist_type,
            acl_level=gist_acl_level,
            files=files)
        response = api_call(self.app, params)

        try:
            assert_error(id_, expected, given=response.body)
        finally:
            Fixture().destroy_gists()

    @mock.patch.object(GistModel, 'create', crash)
    def test_api_create_gist_exception_occurred(self):
        id_, params = build_data(self.apikey_regular, 'create_gist', files={})
        response = api_call(self.app, params)
        expected = 'failed to create gist'
        assert_error(id_, expected, given=response.body)
