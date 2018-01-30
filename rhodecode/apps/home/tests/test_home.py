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

import rhodecode
from rhodecode.model.db import Repository
from rhodecode.model.meta import Session
from rhodecode.model.repo import RepoModel
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.settings import SettingsModel
from rhodecode.tests import TestController
from rhodecode.tests.fixture import Fixture
from rhodecode.lib import helpers as h

fixture = Fixture()


def route_path(name, **kwargs):
    return {
        'home': '/',
        'repo_group_home': '/{repo_group_name}'
    }[name].format(**kwargs)


class TestHomeController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(route_path('home'))
        # if global permission is set
        response.mustcontain('Add Repository')

        # search for objects inside the JavaScript JSON
        for repo in Repository.getAll():
            response.mustcontain('"name_raw": "%s"' % repo.repo_name)

    def test_index_contains_statics_with_ver(self):
        from rhodecode.lib.base import calculate_version_hash

        self.log_user()
        response = self.app.get(route_path('home'))

        rhodecode_version_hash = calculate_version_hash(
            {'beaker.session.secret':'test-rc-uytcxaz'})
        response.mustcontain('style.css?ver={0}'.format(rhodecode_version_hash))
        response.mustcontain('rhodecode-components.js?ver={0}'.format(
            rhodecode_version_hash))

    def test_index_contains_backend_specific_details(self, backend):
        self.log_user()
        response = self.app.get(route_path('home'))
        tip = backend.repo.get_commit().raw_id

        # html in javascript variable:
        response.mustcontain(r'<i class=\"icon-%s\"' % (backend.alias, ))
        response.mustcontain(r'href=\"/%s\"' % (backend.repo_name, ))

        response.mustcontain("""/%s/changeset/%s""" % (backend.repo_name, tip))
        response.mustcontain("""Added a symlink""")

    def test_index_with_anonymous_access_disabled(self):
        with fixture.anon_access(False):
            response = self.app.get(route_path('home'), status=302)
            assert 'login' in response.location

    def test_index_page_on_groups(self, autologin_user, repo_group):
        response = self.app.get(route_path('repo_group_home', repo_group_name='gr1'))
        response.mustcontain("gr1/repo_in_group")

    def test_index_page_on_group_with_trailing_slash(
            self, autologin_user, repo_group):
        response = self.app.get(route_path('repo_group_home', repo_group_name='gr1') + '/')
        response.mustcontain("gr1/repo_in_group")

    @pytest.fixture(scope='class')
    def repo_group(self, request):
        gr = fixture.create_repo_group('gr1')
        fixture.create_repo(name='gr1/repo_in_group', repo_group=gr)

        @request.addfinalizer
        def cleanup():
            RepoModel().delete('gr1/repo_in_group')
            RepoGroupModel().delete(repo_group='gr1', force_delete=True)
            Session().commit()

    def test_index_with_name_with_tags(self, user_util, autologin_user):
        user = user_util.create_user()
        username = user.username
        user.name = '<img src="/image1" onload="alert(\'Hello, World!\');">'
        user.lastname = '#"><img src=x onerror=prompt(document.cookie);>'

        Session().add(user)
        Session().commit()
        user_util.create_repo(owner=username)

        response = self.app.get(route_path('home'))
        response.mustcontain(h.html_escape(user.first_name))
        response.mustcontain(h.html_escape(user.last_name))

    @pytest.mark.parametrize("name, state", [
        ('Disabled', False),
        ('Enabled', True),
    ])
    def test_index_show_version(self, autologin_user, name, state):
        version_string = 'RhodeCode Enterprise %s' % rhodecode.__version__

        sett = SettingsModel().create_or_update_setting(
            'show_version', state, 'bool')
        Session().add(sett)
        Session().commit()
        SettingsModel().invalidate_settings_cache()

        response = self.app.get(route_path('home'))
        if state is True:
            response.mustcontain(version_string)
        if state is False:
            response.mustcontain(no=[version_string])

    def test_logout_form_contains_csrf(self, autologin_user, csrf_token):
        response = self.app.get(route_path('home'))
        assert_response = response.assert_response()
        element = assert_response.get_element('.logout #csrf_token')
        assert element.value == csrf_token
