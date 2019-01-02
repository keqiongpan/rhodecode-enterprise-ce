# -*- coding: utf-8 -*-

# Copyright (C) 2016-2019 RhodeCode GmbH
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
import re
import colander

from rhodecode.model.validation_schema import types, validators
from rhodecode.translation import _


@colander.deferred
def deferred_user_group_name_validator(node, kw):

    def name_validator(node, value):

        msg = _('Allowed in name are letters, numbers, and `-`, `_`, `.` '
                'Name must start with a letter or number. Got `{}`').format(value)

        if not re.match(r'^[a-zA-Z0-9]{1}[a-zA-Z0-9\-\_\.]+$', value):
            raise colander.Invalid(node, msg)

    return name_validator


@colander.deferred
def deferred_user_group_owner_validator(node, kw):

    def owner_validator(node, value):
        from rhodecode.model.db import User
        existing = User.get_by_username(value)
        if not existing:
            msg = _(u'User group owner with id `{}` does not exists').format(value)
            raise colander.Invalid(node, msg)

    return owner_validator


class UserGroupSchema(colander.Schema):

    user_group_name = colander.SchemaNode(
        colander.String(),
        validator=deferred_user_group_name_validator)

    user_group_description = colander.SchemaNode(
        colander.String(), missing='')

    user_group_owner = colander.SchemaNode(
        colander.String(),
        validator=deferred_user_group_owner_validator)

    user_group_active = colander.SchemaNode(
        types.StringBooleanType(),
        missing=False)

    def deserialize(self, cstruct):
        """
        Custom deserialize that allows to chain validation, and verify
        permissions, and as last step uniqueness
        """

        appstruct = super(UserGroupSchema, self).deserialize(cstruct)
        return appstruct
