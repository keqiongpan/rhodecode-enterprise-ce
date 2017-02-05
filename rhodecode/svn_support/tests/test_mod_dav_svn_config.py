# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 RhodeCode GmbH
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
import re

from pyramid import testing

from rhodecode.svn_support import utils


class TestModDavSvnConfig(object):

    @classmethod
    def setup_class(cls):
        # Make mako renderer available in tests.
        config = testing.setUp()
        config.include('pyramid_mako')

        cls.location_root = u'/location/root/çµäö'
        cls.parent_path_root = u'/parent/path/çµäö'
        cls.realm = u'Dummy Realm (äöüçµ)'

    @classmethod
    def get_repo_group_mocks(cls, count=1):
        repo_groups = []
        for num in range(0, count):
            full_path = u'/path/to/RepöGröúp-°µ {}'.format(num)
            repo_group_mock = mock.MagicMock()
            repo_group_mock.full_path = full_path
            repo_group_mock.full_path_splitted = full_path.split('/')
            repo_groups.append(repo_group_mock)
        return repo_groups

    def assert_root_location_directive(self, config):
        pattern = u'<Location "{location}">'.format(
            location=self.location_root)
        assert len(re.findall(pattern, config)) == 1

    def assert_group_location_directive(self, config, group_path):
        pattern = u'<Location "{location}{group_path}">'.format(
            location=self.location_root, group_path=group_path)
        assert len(re.findall(pattern, config)) == 1

    def test_render_mod_dav_svn_config(self):
        repo_groups = self.get_repo_group_mocks(count=10)
        generated_config = utils._render_mod_dav_svn_config(
            parent_path_root=self.parent_path_root,
            list_parent_path=True,
            location_root=self.location_root,
            repo_groups=repo_groups,
            realm=self.realm,
            use_ssl=True
        )
        # Assert that one location directive exists for each repository group.
        for group in repo_groups:
            self.assert_group_location_directive(
                generated_config, group.full_path)

        # Assert that the root location directive exists.
        self.assert_root_location_directive(generated_config)

    @pytest.mark.parametrize('list_parent_path', [True, False])
    @pytest.mark.parametrize('use_ssl', [True, False])
    def test_list_parent_path(self, list_parent_path, use_ssl):
        generated_config = utils._render_mod_dav_svn_config(
            parent_path_root=self.parent_path_root,
            list_parent_path=list_parent_path,
            location_root=self.location_root,
            repo_groups=self.get_repo_group_mocks(count=10),
            realm=self.realm,
            use_ssl=use_ssl
        )

        # Assert that correct configuration directive is present.
        if list_parent_path:
            assert not re.search('SVNListParentPath\s+Off', generated_config)
            assert re.search('SVNListParentPath\s+On', generated_config)
        else:
            assert re.search('SVNListParentPath\s+Off', generated_config)
            assert not re.search('SVNListParentPath\s+On', generated_config)

        if use_ssl:
            assert 'RequestHeader edit Destination ^https: http: early' \
                   in generated_config
        else:
            assert '#RequestHeader edit Destination ^https: http: early' \
                   in generated_config
