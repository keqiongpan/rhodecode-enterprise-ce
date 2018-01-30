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
from rhodecode.model.db import Repository


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'branches_home': '/{repo_name}/branches',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.usefixtures('autologin_user', 'app')
class TestBranchesController(object):

    def test_index(self, backend):
        response = self.app.get(
            route_path('branches_home', repo_name=backend.repo_name))

        repo = Repository.get_by_repo_name(backend.repo_name)

        for commit_id, obj_name in repo.scm_instance().branches.items():
            assert commit_id in response
            assert obj_name in response
