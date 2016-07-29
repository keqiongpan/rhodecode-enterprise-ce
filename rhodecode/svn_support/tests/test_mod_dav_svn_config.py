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

from rhodecode.svn_support import config_keys, utils


class TestModDavSvnConfig(object):
    @classmethod
    def setup_class(cls):
        # Make mako renderer available in tests.
        config = testing.setUp()
        config.include('pyramid_mako')

        # Temporary directory holding the generated config files.
        cls.tempdir = tempfile.mkdtemp(suffix='pytest-mod-dav-svn')

        cls.location_root = '/location/root'
        cls.parent_path_root = '/parent/path/root'

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
            config_keys.location_root: cls.location_root,
            config_keys.parent_path_root: cls.parent_path_root,
            config_keys.list_parent_path: True,
        }

    @classmethod
    def get_repo_groups(cls, count=1):
        repo_groups = []
        for num in range(0, count):
            full_path = '/path/to/RepoGroup{}'.format(num)
            repo_group_mock = mock.MagicMock()
            repo_group_mock.full_path = full_path
            repo_group_mock.full_path_splitted = full_path.split('/')
            repo_groups.append(repo_group_mock)
        return repo_groups

    def assert_root_location_directive(self, config):
        pattern = '<Location {location}>'.format(location=self.location_root)
        assert len(re.findall(pattern, config)) == 1

    def assert_group_location_directive(self, config, group_path):
        pattern = '<Location {location}{group_path}>'.format(
            location=self.location_root, group_path=group_path)
        assert len(re.findall(pattern, config)) == 1

    @mock.patch('rhodecode.svn_support.utils.RepoGroup')
    def test_generate_mod_dav_svn_config(self, RepoGroupMock):
        num_groups = 3
        RepoGroupMock.get_all_repo_groups.return_value = self.get_repo_groups(
            count=num_groups)

        # Execute the method under test.
        settings = self.get_settings()
        utils.generate_mod_dav_svn_config(settings)

        # Read generated file.
        with open(settings[config_keys.config_file_path], 'r') as file_:
            content = file_.read()

        # Assert that one location directive exists for each repository group.
        for group in self.get_repo_groups(count=num_groups):
            self.assert_group_location_directive(content, group.full_path)

        # Assert that the root location directive exists.
        self.assert_root_location_directive(content)

    @mock.patch('rhodecode.svn_support.utils.RepoGroup')
    def test_list_parent_path_on(self, RepoGroupMock):
        RepoGroupMock.get_all_repo_groups.return_value = self.get_repo_groups()

        # Execute the method under test.
        settings = self.get_settings()
        settings[config_keys.list_parent_path] = True
        utils.generate_mod_dav_svn_config(settings)

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
        utils.generate_mod_dav_svn_config(settings)

        # Read generated file.
        with open(settings[config_keys.config_file_path], 'r') as file_:
            content = file_.read()

        # Make assertions.
        assert re.search('SVNListParentPath\s+Off', content)
        assert not re.search('SVNListParentPath\s+On', content)

    @mock.patch('rhodecode.svn_support.utils.log')
    def test_write_does_not_raise_on_error(self, LogMock):
        """
        Writing the configuration to file should never raise exceptions.
        If e.g. path points to a place without write permissions.
        """
        utils._write_mod_dav_svn_config(
            'content', '/dev/null/not/existing/path')

        # Assert that we log the exception.
        assert LogMock.exception.called
