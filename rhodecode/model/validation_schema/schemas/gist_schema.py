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

import os

import colander

from rhodecode.translation import _
from rhodecode.model.validation_schema import preparers


def nodes_to_sequence(nodes, colander_node=None):
    """
    Converts old style dict nodes to new list of dicts

    :param nodes: dict with key beeing name of the file

    """
    if not isinstance(nodes, dict):
        msg = 'Nodes needs to be a dict, got {}'.format(type(nodes))
        raise colander.Invalid(colander_node, msg)
    out = []

    for key, val in nodes.items():
        val = (isinstance(val, dict) and val) or {}
        out.append(dict(
            filename=key,
            content=val.get('content'),
            mimetype=val.get('mimetype')
        ))

    out = Nodes().deserialize(out)
    return out


def sequence_to_nodes(nodes, colander_node=None):
    if not isinstance(nodes, list):
        msg = 'Nodes needs to be a list, got {}'.format(type(nodes))
        raise colander.Invalid(colander_node, msg)
    nodes = Nodes().deserialize(nodes)

    out = {}
    try:
        for file_data in nodes:
            file_data_skip = file_data.copy()
            # if we got filename_org we use it as a key so we keep old
            # name as input and rename is-reflected inside the values as
            # filename and filename_org differences.
            filename_org = file_data.get('filename_org')
            filename = filename_org or file_data['filename']
            out[filename] = {}
            out[filename].update(file_data_skip)

    except Exception as e:
        msg = 'Invalid data format org_exc:`{}`'.format(repr(e))
        raise colander.Invalid(colander_node, msg)
    return out


@colander.deferred
def deferred_lifetime_validator(node, kw):
    options = kw.get('lifetime_options', [])
    return colander.All(
        colander.Range(min=-1, max=60 * 24 * 30 * 12),
        colander.OneOf([x for x in options]))


def unique_gist_validator(node, value):
    from rhodecode.model.db import Gist
    existing = Gist.get_by_access_id(value)
    if existing:
        msg = _(u'Gist with name {} already exists').format(value)
        raise colander.Invalid(node, msg)


def filename_validator(node, value):
    if value != os.path.basename(value):
        msg = _(u'Filename {} cannot be inside a directory').format(value)
        raise colander.Invalid(node, msg)


class NodeSchema(colander.MappingSchema):
    # if we perform rename this will be org filename
    filename_org = colander.SchemaNode(
        colander.String(),
        preparer=[preparers.strip_preparer,
                  preparers.non_ascii_strip_preparer],
        validator=filename_validator,
        missing=None)

    filename = colander.SchemaNode(
        colander.String(),
        preparer=[preparers.strip_preparer,
                  preparers.non_ascii_strip_preparer],
        validator=filename_validator)

    content = colander.SchemaNode(
        colander.String())
    mimetype = colander.SchemaNode(
        colander.String(),
        missing=None)


class Nodes(colander.SequenceSchema):
    filenames = NodeSchema()

    def validator(self, node, cstruct):
        if not isinstance(cstruct, list):
            return

        found_filenames = []
        for data in cstruct:
            filename = data['filename']
            if filename in found_filenames:
                msg = _('Duplicated value for filename found: `{}`').format(
                    filename)
                raise colander.Invalid(node, msg)
            found_filenames.append(filename)


class GistSchema(colander.MappingSchema):
    """
    schema = GistSchema()
    schema.bind(
        lifetime_options = [1,2,3]
    )
    out = schema.deserialize(dict(
        nodes=[
            {'filename': 'x', 'content': 'xxx', },
            {'filename': 'docs/Z', 'content': 'xxx', 'mimetype': 'x'},
        ]
    ))
    """

    from rhodecode.model.db import Gist

    gistid = colander.SchemaNode(
        colander.String(),
        missing=None,
        preparer=[preparers.strip_preparer,
                  preparers.non_ascii_strip_preparer,
                  preparers.slugify_preparer],
        validator=colander.All(
            colander.Length(min=3),
            unique_gist_validator
        ))

    description = colander.SchemaNode(
        colander.String(),
        missing=u'')

    lifetime = colander.SchemaNode(
        colander.Integer(),
        validator=deferred_lifetime_validator)

    gist_acl_level = colander.SchemaNode(
        colander.String(),
        validator=colander.OneOf([Gist.ACL_LEVEL_PUBLIC,
                                  Gist.ACL_LEVEL_PRIVATE]))

    gist_type = colander.SchemaNode(
        colander.String(),
        missing=Gist.GIST_PUBLIC,
        validator=colander.OneOf([Gist.GIST_PRIVATE, Gist.GIST_PUBLIC]))

    nodes = Nodes()
