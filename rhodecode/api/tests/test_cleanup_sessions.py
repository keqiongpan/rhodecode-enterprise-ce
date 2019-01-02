# -*- coding: utf-8 -*-

# Copyright (C) 2017-2019 RhodeCode GmbH
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

from rhodecode.lib.user_sessions import FileAuthSessions
from rhodecode.api.tests.utils import (
    build_data, api_call, assert_ok, assert_error, crash)


@pytest.mark.usefixtures("testuser_api", "app")
class TestCleanupSessions(object):
    def test_api_cleanup_sessions(self):
        id_, params = build_data(self.apikey, 'cleanup_sessions')
        response = api_call(self.app, params)

        expected = {'backend': 'file sessions', 'sessions_removed': 0}
        assert_ok(id_, expected, given=response.body)

    @mock.patch.object(FileAuthSessions, 'clean_sessions', crash)
    def test_api_cleanup_error(self):
        id_, params = build_data(self.apikey, 'cleanup_sessions', )
        response = api_call(self.app, params)

        expected = 'Error occurred during session cleanup'
        assert_error(id_, expected, given=response.body)
