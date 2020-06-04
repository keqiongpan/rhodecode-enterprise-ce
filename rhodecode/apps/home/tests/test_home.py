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

import rhodecode
from rhodecode.model.db import Repository, RepoGroup, User
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
        'main_page_repos_data': '/_home_repos',
        'main_page_repo_groups_data': '/_home_repo_groups',
        'repo_group_home': '/{repo_group_name}'
    }[name].format(**kwargs)


class TestHomeController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(route_path('home'))
        # if global permission is set
        response.mustcontain('New Repository')

    def test_index_grid_repos(self, xhr_header):
        self.log_user()
        response = self.app.get(route_path('main_page_repos_data'), extra_environ=xhr_header)
        # search for objects inside the JavaScript JSON
        for obj in Repository.getAll():
            response.mustcontain('<a href=\\"/{}\\">'.format(obj.repo_name))

    def test_index_grid_repo_groups(self, xhr_header):
        self.log_user()
        response = self.app.get(route_path('main_page_repo_groups_data'),
                                extra_environ=xhr_header,)

        # search for objects inside the JavaScript JSON
        for obj in RepoGroup.getAll():
            response.mustcontain('<a href=\\"/{}\\">'.format(obj.group_name))

    def test_index_grid_repo_groups_without_access(self, xhr_header, user_util):
        user = user_util.create_user(password='qweqwe')
        group_ok = user_util.create_repo_group(owner=user)
        group_id_ok = group_ok.group_id

        group_forbidden = user_util.create_repo_group(owner=User.get_first_super_admin())
        group_id_forbidden = group_forbidden.group_id

        user_util.grant_user_permission_to_repo_group(group_forbidden, user, 'group.none')
        self.log_user(user.username, 'qweqwe')

        self.app.get(route_path('main_page_repo_groups_data'),
                     extra_environ=xhr_header,
                     params={'repo_group_id': group_id_ok}, status=200)

        self.app.get(route_path('main_page_repo_groups_data'),
                     extra_environ=xhr_header,
                     params={'repo_group_id': group_id_forbidden}, status=404)

    def test_index_contains_statics_with_ver(self):
        from rhodecode.lib.base import calculate_version_hash

        self.log_user()
        response = self.app.get(route_path('home'))

        rhodecode_version_hash = calculate_version_hash(
            {'beaker.session.secret': 'test-rc-uytcxaz'})
        response.mustcontain('style.css?ver={0}'.format(rhodecode_version_hash))
        response.mustcontain('scripts.min.js?ver={0}'.format(rhodecode_version_hash))

    def test_index_contains_backend_specific_details(self, backend, xhr_header):
        self.log_user()
        response = self.app.get(route_path('main_page_repos_data'), extra_environ=xhr_header)
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

    def test_index_page_on_groups_with_wrong_group_id(self, autologin_user, xhr_header):
        group_id = 918123
        self.app.get(
            route_path('main_page_repo_groups_data'),
            params={'repo_group_id': group_id},
            status=404, extra_environ=xhr_header)

    def test_index_page_on_groups(self, autologin_user, user_util, xhr_header):
        gr = user_util.create_repo_group()
        repo = user_util.create_repo(parent=gr)
        repo_name = repo.repo_name
        group_id = gr.group_id

        response = self.app.get(route_path(
            'repo_group_home', repo_group_name=gr.group_name))
        response.mustcontain('d.repo_group_id = {}'.format(group_id))

        response = self.app.get(
            route_path('main_page_repos_data'),
            params={'repo_group_id': group_id},
            extra_environ=xhr_header,)
        response.mustcontain(repo_name)

    def test_index_page_on_group_with_trailing_slash(self, autologin_user, user_util, xhr_header):
        gr = user_util.create_repo_group()
        repo = user_util.create_repo(parent=gr)
        repo_name = repo.repo_name
        group_id = gr.group_id

        response = self.app.get(route_path(
            'repo_group_home', repo_group_name=gr.group_name+'/'))
        response.mustcontain('d.repo_group_id = {}'.format(group_id))

        response = self.app.get(
            route_path('main_page_repos_data'),
            params={'repo_group_id': group_id},
            extra_environ=xhr_header, )
        response.mustcontain(repo_name)

    @pytest.mark.parametrize("name, state", [
        ('Disabled', False),
        ('Enabled', True),
    ])
    def test_index_show_version(self, autologin_user, name, state):
        version_string = 'RhodeCode %s' % rhodecode.__version__

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
        element = assert_response.get_element('.logout [name=csrf_token]')
        assert element.value == csrf_token
