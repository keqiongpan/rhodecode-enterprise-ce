# -*- coding: utf-8 -*-

# Copyright (C) 2016-2016  RhodeCode GmbH
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
import re
import shutil
import tempfile

from pyramid import testing

from rhodecode.svn_support import config_keys
from rhodecode.svn_support.utils import generate_mod_dav_svn_config


class TestModDavSvnConfig(object):
    @classmethod
    def setup_class(cls):
        # Make mako renderer available in tests.
        config = testing.setUp()
        config.include('pyramid_mako')

        # Temporary directory holding the generated config files.
        cls.tempdir = tempfile.mkdtemp(suffix='pytest-mod-dav-svn')

        # Regex pattern to match a location block in the generated config.
        cls.location_regex = (
            '<Location {location}>\s+'
            'DAV svn\s+'
            'SVNParentPath {svn_parent_path}\s+'
            'SVNListParentPath {svn_list_parent_path}\s+'
            'Allow from all\s+'
            'Order allow,deny\s+'
            '</Location>')

    @classmethod
    def teardown_class(cls):
        testing.tearDown()
        shutil.rmtree(cls.tempdir, ignore_errors=True)

    @classmethod
    def get_settings(cls):
        config_file_path = tempfile.mkstemp(
            suffix='mod-dav-svn.conf', dir=cls.tempdir)[1]
        return {
            config_keys.config_file_path: config_file_path,
            config_keys.location_root: '/location/root/',
            config_keys.parent_path_root: '/parent/path/root/',
            config_keys.list_parent_path: True,
        }

    @classmethod
    def get_repo_groups(cls, count=1):
        repo_groups = []
        for num in range(0, count):
            repo_group_mock = mock.MagicMock()
            repo_group_mock.full_path = '/path/to/RepoGroup{}'.format(num)
            repo_groups.append(repo_group_mock)
        return repo_groups

    @mock.patch('rhodecode.svn_support.utils.RepoGroup')
    def test_generate_mod_dav_svn_config(self, RepoGroupMock):
        num_groups = 3
        RepoGroupMock.get_all_repo_groups.return_value = self.get_repo_groups(
            count=num_groups)

        # Execute the method under test.
        settings = self.get_settings()
        generate_mod_dav_svn_config(settings)

        # Read generated file.
        with open(settings[config_keys.config_file_path], 'r') as file_:
            content = file_.read()

        # Assert that one location block exists for each repository group.
        repo_group_pattern = self.location_regex.format(
            location='/location/root/path/to/RepoGroup\d+',
            svn_parent_path='/parent/path/root/path/to/RepoGroup\d+',
            svn_list_parent_path='On')
        assert len(re.findall(repo_group_pattern, content)) == num_groups

        # Assert that the root location block exists.
        root_pattern = self.location_regex.format(
            location='/location/root/',
            svn_parent_path='/parent/path/root/',
            svn_list_parent_path='On')
        assert len(re.findall(root_pattern, content)) == 1

    @mock.patch('rhodecode.svn_support.utils.RepoGroup')
    def test_list_parent_path_on(self, RepoGroupMock):
        RepoGroupMock.get_all_repo_groups.return_value = self.get_repo_groups()

        # Execute the method under test.
        settings = self.get_settings()
        settings[config_keys.list_parent_path] = True
        generate_mod_dav_svn_config(settings)

        # Read generated file.
        with open(settings[config_keys.config_file_path], 'r') as file_:
            content = file_.read()

        # Make assertions.
        assert not re.search('SVNListParentPath\s+Off', content)
        assert re.search('SVNListParentPath\s+On', content)

    @mock.patch('rhodecode.svn_support.utils.RepoGroup')
    def test_list_parent_path_off(self, RepoGroupMock):
        RepoGroupMock.get_all_repo_groups.return_value = self.get_repo_groups()

        # Execute the method under test.
        settings = self.get_settings()
        settings[config_keys.list_parent_path] = False
        generate_mod_dav_svn_config(settings)

        # Read generated file.
        with open(settings[config_keys.config_file_path], 'r') as file_:
            content = file_.read()

        # Make assertions.
        assert re.search('SVNListParentPath\s+Off', content)
        assert not re.search('SVNListParentPath\s+On', content)
