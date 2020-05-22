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

from rhodecode.model import validation_schema
from rhodecode.model.validation_schema.schemas import gist_schema


class TestGistSchema(object):

    def test_deserialize_bad_data(self):
        schema = gist_schema.GistSchema().bind(
            lifetime_options=[1, 2, 3]
        )
        with pytest.raises(validation_schema.Invalid) as exc_info:
            schema.deserialize('err')
        err = exc_info.value.asdict()
        assert err[''] == '"err" is not a mapping type: ' \
                          'Does not implement dict-like functionality.'

    def test_deserialize_bad_lifetime_options(self):
        schema = gist_schema.GistSchema().bind(
            lifetime_options=[1, 2, 3]
        )
        with pytest.raises(validation_schema.Invalid) as exc_info:
            schema.deserialize(dict(
                lifetime=10
            ))
        err = exc_info.value.asdict()
        assert err['lifetime'] == '"10" is not one of 1, 2, 3'

        with pytest.raises(validation_schema.Invalid) as exc_info:
            schema.deserialize(dict(
                lifetime='x'
            ))
        err = exc_info.value.asdict()
        assert err['lifetime'] == '"x" is not a number'

    def test_serialize_data_correctly(self):
        schema = gist_schema.GistSchema().bind(
            lifetime_options=[1, 2, 3]
        )
        nodes = [{
            'filename': 'foobar',
            'filename_org': 'foobar',
            'content': 'content',
            'mimetype': 'xx'
        }]
        schema_data = schema.deserialize(dict(
            lifetime=2,
            gist_type='public',
            gist_acl_level='acl_public',
            nodes=nodes,
        ))

        assert schema_data['nodes'] == nodes

    def test_serialize_data_correctly_with_conversion(self):
        schema = gist_schema.GistSchema().bind(
            lifetime_options=[1, 2, 3],
            convert_nodes=True
        )
        nodes = [{
            'filename': 'foobar',
            'filename_org': None,
            'content': 'content',
            'mimetype': 'xx'
        }]
        schema_data = schema.deserialize(dict(
            lifetime=2,
            gist_type='public',
            gist_acl_level='acl_public',
            nodes=nodes,
        ))

        assert schema_data['nodes'] == nodes

        seq_nodes = gist_schema.sequence_to_nodes(nodes)
        assert isinstance(seq_nodes, dict)
        seq_nodes = gist_schema.nodes_to_sequence(seq_nodes)
        assert nodes == seq_nodes
