# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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

from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.api.tests.utils import build_data, api_call, assert_ok, jsonify


@pytest.mark.usefixtures("testuser_api", "app")
class TestApiGetRepoGroups(object):
    def test_api_get_repo_groups(self):
        id_, params = build_data(self.apikey, 'get_repo_groups')
        response = api_call(self.app, params)

        result = []
        for repo in RepoGroupModel().get_all():
            result.append(repo.get_api_data())
        ret = jsonify(result)

        expected = ret
        assert_ok(id_, expected, given=response.body)
