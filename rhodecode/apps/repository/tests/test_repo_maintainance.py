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

import mock
import pytest

from rhodecode.lib.utils2 import str2bool
from rhodecode.lib.vcs.exceptions import RepositoryRequirementError
from rhodecode.model.db import Repository, UserRepoToPerm, Permission, User
from rhodecode.model.meta import Session
from rhodecode.tests import (
    TEST_USER_ADMIN_LOGIN, TEST_USER_REGULAR_LOGIN, assert_session_flash)
from rhodecode.tests.fixture import Fixture

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'edit_repo_maintenance': '/{repo_name}/settings/maintenance',
        'edit_repo_maintenance_execute': '/{repo_name}/settings/maintenance/execute',

    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


def _get_permission_for_user(user, repo):
    perm = UserRepoToPerm.query()\
        .filter(UserRepoToPerm.repository ==
                Repository.get_by_repo_name(repo))\
        .filter(UserRepoToPerm.user == User.get_by_username(user))\
        .all()
    return perm


@pytest.mark.usefixtures('autologin_user', 'app')
class TestAdminRepoMaintenance(object):
    @pytest.mark.parametrize('urlname', [
        'edit_repo_maintenance',
    ])
    def test_show_page(self, urlname, app, backend):
        app.get(route_path(urlname, repo_name=backend.repo_name), status=200)

    def test_execute_maintenance_for_repo_hg(self, app, backend_hg, autologin_user, xhr_header):
        repo_name = backend_hg.repo_name

        response = app.get(
            route_path('edit_repo_maintenance_execute',
                       repo_name=repo_name,),
            extra_environ=xhr_header)

        assert "HG Verify repo" in ''.join(response.json)
