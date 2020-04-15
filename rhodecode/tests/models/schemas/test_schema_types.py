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

from rhodecode.model.validation_schema.types import (
    GroupNameType, RepoNameType, StringBooleanType)


class TestGroupNameType(object):
    @pytest.mark.parametrize('given, expected', [
        ('//group1/group2//', 'group1/group2'),
        ('//group1///group2//', 'group1/group2'),
        ('group1/group2///group3', 'group1/group2/group3'),
    ])
    def test_normalize_path(self, given, expected):
        result = GroupNameType()._normalize(given)
        assert result == expected

    @pytest.mark.parametrize('given, expected', [
        ('//group1/group2//', 'group1/group2'),
        ('//group1///group2//', 'group1/group2'),
        ('group1/group2///group3', 'group1/group2/group3'),
        ('v1.2', 'v1.2'),
        ('/v1.2', 'v1.2'),
        ('.dirs', '.dirs'),
        ('..dirs', '.dirs'),
        ('./..dirs', '.dirs'),
        ('dir/;name;/;[];/sub', 'dir/name/sub'),
        (',/,/,d,,,', 'd'),
        ('/;/#/,d,,,', 'd'),
        ('long../../..name', 'long./.name'),
        ('long../..name', 'long./.name'),
        ('../', ''),
        ('\'../"../', ''),
        ('c,/,/..//./,c,,,/.d/../.........c', 'c/c/.d/.c'),
        ('c,/,/..//./,c,,,', 'c/c'),
        ('d../..d', 'd./.d'),
        ('d../../d', 'd./d'),

        ('d\;\./\,\./d', 'd./d'),
        ('d\.\./\.\./d', 'd./d'),
        ('d\.\./\..\../d', 'd./d'),
    ])
    def test_deserialize_clean_up_name(self, given, expected):
        class TestSchema(colander.Schema):
            field_group = colander.SchemaNode(GroupNameType())
            field_repo = colander.SchemaNode(RepoNameType())

        schema = TestSchema()
        cleaned_data = schema.deserialize({
            'field_group': given,
            'field_repo': given
        })
        assert cleaned_data['field_group'] == expected
        assert cleaned_data['field_repo'] == expected


class TestStringBooleanType(object):

    def _get_schema(self):
        class Schema(colander.MappingSchema):
            bools = colander.SchemaNode(StringBooleanType())
        return Schema()

    @pytest.mark.parametrize('given, expected', [
        ('1', True),
        ('yEs', True),
        ('true', True),

        ('0', False),
        ('NO', False),
        ('FALSE', False),

    ])
    def test_convert_type(self, given, expected):
        schema = self._get_schema()
        result = schema.deserialize({'bools':given})
        assert result['bools'] == expected

    def test_try_convert_bad_type(self):
        schema = self._get_schema()
        with pytest.raises(colander.Invalid):
            result = schema.deserialize({'bools': 'boom'})
