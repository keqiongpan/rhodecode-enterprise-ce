# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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

import colander
import pytest

from rhodecode.model.validation_schema import types
from rhodecode.model.validation_schema.schemas import repo_schema


class TestRepoSchema(object):

    #TODO:
    # test nested groups

    @pytest.mark.parametrize('given, expected', [
        ('my repo', 'my-repo'),
        (' hello   world mike ', 'hello-world-mike'),

        ('//group1/group2//', 'group1/group2'),
        ('//group1///group2//', 'group1/group2'),
        ('///group1/group2///group3', 'group1/group2/group3'),
        ('word g1/group2///group3', 'word-g1/group2/group3'),

        ('grou p1/gro;,,##up2//.../group3', 'grou-p1/group2/group3'),

        ('group,,,/,,,/1/2/3', 'group/1/2/3'),
        ('grou[]p1/gro;up2///gro up3', 'group1/group2/gro-up3'),
        (u'grou[]p1/gro;up2///gro up3/ąć', u'group1/group2/gro-up3/ąć'),
    ])
    def test_deserialize_repo_name(self, app, user_admin, given, expected):

        schema = repo_schema.RepoSchema().bind()
        assert expected == schema.get('repo_name').deserialize(given)

    def test_deserialize(self, app, user_admin):
        schema = repo_schema.RepoSchema().bind(
            repo_type_options=['hg'],
            repo_type='hg',
            user=user_admin
        )

        schema_data = schema.deserialize(dict(
            repo_name='my_schema_repo',
            repo_type='hg',
            repo_owner=user_admin.username
        ))

        assert schema_data['repo_name'] == u'my_schema_repo'
        assert schema_data['repo_group'] == {
            'repo_group_id': None,
            'repo_group_name': types.RootLocation,
            'repo_name_with_group': u'my_schema_repo',
            'repo_name_without_group': u'my_schema_repo'}

    @pytest.mark.parametrize('given, err_key, expected_exc', [
        ('xxx/my_schema_repo','repo_group', 'Repository group `xxx` does not exist'),
        ('', 'repo_name', 'Name must start with a letter or number. Got ``'),
    ])
    def test_deserialize_with_bad_group_name(
            self, app, user_admin, given, err_key, expected_exc):

        schema = repo_schema.RepoSchema().bind(
            repo_type_options=['hg'],
            repo_type='hg',
            user=user_admin
        )

        with pytest.raises(colander.Invalid) as excinfo:
            schema.deserialize(dict(
                repo_name=given,
                repo_type='hg',
                repo_owner=user_admin.username
            ))

        assert excinfo.value.asdict()[err_key] == expected_exc

    def test_deserialize_with_group_name(self, app, user_admin, test_repo_group):
        schema = repo_schema.RepoSchema().bind(
            repo_type_options=['hg'],
            repo_type='hg',
            user=user_admin
        )

        full_name = test_repo_group.group_name + u'/my_schema_repo'
        schema_data = schema.deserialize(dict(
            repo_name=full_name,
            repo_type='hg',
            repo_owner=user_admin.username
        ))

        assert schema_data['repo_name'] == full_name
        assert schema_data['repo_group'] == {
            'repo_group_id': test_repo_group.group_id,
            'repo_group_name': test_repo_group.group_name,
            'repo_name_with_group': full_name,
            'repo_name_without_group': u'my_schema_repo'}

    def test_deserialize_with_group_name_regular_user_no_perms(
            self, app, user_regular, test_repo_group):
        schema = repo_schema.RepoSchema().bind(
            repo_type_options=['hg'],
            repo_type='hg',
            user=user_regular
        )

        full_name = test_repo_group.group_name + '/my_schema_repo'
        with pytest.raises(colander.Invalid) as excinfo:
            schema.deserialize(dict(
                repo_name=full_name,
                repo_type='hg',
                repo_owner=user_regular.username
            ))

        expected = 'Repository group `{}` does not exist'.format(
            test_repo_group.group_name)
        assert excinfo.value.asdict()['repo_group'] == expected
