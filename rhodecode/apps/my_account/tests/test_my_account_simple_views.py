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

from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.model.db import User, UserEmailMap, Repository, UserFollowing
from rhodecode.tests import (
    TestController, TEST_USER_ADMIN_LOGIN, TEST_USER_REGULAR_EMAIL,
    assert_session_flash)
from rhodecode.tests.fixture import Fixture

fixture = Fixture()


def route_path(name, **kwargs):
    return {
        'my_account_repos':
            ADMIN_PREFIX + '/my_account/repos',
        'my_account_watched':
            ADMIN_PREFIX + '/my_account/watched',
        'my_account_perms':
            ADMIN_PREFIX + '/my_account/perms',
        'my_account_notifications':
            ADMIN_PREFIX + '/my_account/notifications',
    }[name].format(**kwargs)


class TestMyAccountSimpleViews(TestController):

    def test_my_account_my_repos(self, autologin_user):
        response = self.app.get(route_path('my_account_repos'))
        repos = Repository.query().filter(
            Repository.user == User.get_by_username(
                TEST_USER_ADMIN_LOGIN)).all()
        for repo in repos:
            response.mustcontain('"name_raw": "%s"' % repo.repo_name)

    def test_my_account_my_watched(self, autologin_user):
        response = self.app.get(route_path('my_account_watched'))

        repos = UserFollowing.query().filter(
            UserFollowing.user == User.get_by_username(
                TEST_USER_ADMIN_LOGIN)).all()
        for repo in repos:
            response.mustcontain(
                '"name_raw": "%s"' % repo.follows_repository.repo_name)

    def test_my_account_perms(self, autologin_user):
        response = self.app.get(route_path('my_account_perms'))
        assert_response = response.assert_response()
        assert assert_response.get_elements('.perm_tag.none')
        assert assert_response.get_elements('.perm_tag.read')
        assert assert_response.get_elements('.perm_tag.write')
        assert assert_response.get_elements('.perm_tag.admin')

    def test_my_account_notifications(self, autologin_user):
        response = self.app.get(route_path('my_account_notifications'))
        response.mustcontain('Test flash message')
