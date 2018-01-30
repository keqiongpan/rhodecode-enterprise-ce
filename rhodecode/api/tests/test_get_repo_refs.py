# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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

from rhodecode.model.meta import Session
from rhodecode.model.repo import RepoModel
from rhodecode.model.user import UserModel
from rhodecode.tests import TEST_USER_ADMIN_LOGIN
from rhodecode.api.tests.utils import (
    build_data, api_call, assert_ok, assert_error, expected_permissions)


@pytest.mark.usefixtures("testuser_api", "app")
class TestGetRepo(object):
    def test_api_get_repo_refs(self, backend, user_util):
        repo = backend.create_repo()
        id_, params = build_data(self.apikey, 'get_repo_refs',
                                 **{'repoid': repo.repo_name,})
        response = api_call(self.app, params)
        expected = repo.scm_instance().refs()
        assert_ok(id_, expected, given=response.body)
