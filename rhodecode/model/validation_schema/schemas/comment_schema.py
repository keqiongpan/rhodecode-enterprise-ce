# -*- coding: utf-8 -*-

# Copyright (C) 2017-2020 RhodeCode GmbH
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
from rhodecode.model.validation_schema import types


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


comment_types = ['note', 'todo']


class CommentSchema(colander.MappingSchema):
    from rhodecode.model.db import ChangesetComment, ChangesetStatus

    comment_body = colander.SchemaNode(colander.String())
    comment_type = colander.SchemaNode(
        colander.String(),
        validator=colander.OneOf(ChangesetComment.COMMENT_TYPES),
        missing=ChangesetComment.COMMENT_TYPE_NOTE)
    is_draft = colander.SchemaNode(colander.Boolean(),missing=False)
    comment_file = colander.SchemaNode(colander.String(), missing=None)
    comment_line = colander.SchemaNode(colander.String(), missing=None)
    status_change = colander.SchemaNode(
        colander.String(), missing=None,
        validator=colander.OneOf([x[0] for x in ChangesetStatus.STATUSES]))
    renderer_type = colander.SchemaNode(colander.String())

    resolves_comment_id = colander.SchemaNode(colander.Integer(), missing=None)

    user = colander.SchemaNode(types.StrOrIntType())
    repo = colander.SchemaNode(types.StrOrIntType())
