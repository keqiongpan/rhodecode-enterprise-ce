# -*- coding: utf-8 -*-

# Copyright (C) 2016-2018 RhodeCode GmbH
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

from rhodecode import forms
from rhodecode.model.db import User
from rhodecode.model.validation_schema import types, validators
from rhodecode.translation import _
from rhodecode.lib.auth import check_password


@colander.deferred
def deferred_user_password_validator(node, kw):
    username = kw.get('username')
    user = User.get_by_username(username)

    def _user_password_validator(node, value):
        if not check_password(value, user.password):
            msg = _('Password is incorrect')
            raise colander.Invalid(node, msg)
    return _user_password_validator


class ChangePasswordSchema(colander.Schema):

    current_password = colander.SchemaNode(
        colander.String(),
        missing=colander.required,
        widget=forms.widget.PasswordWidget(redisplay=True),
        validator=deferred_user_password_validator)

    new_password = colander.SchemaNode(
        colander.String(),
        missing=colander.required,
        widget=forms.widget.CheckedPasswordWidget(redisplay=True),
        validator=colander.Length(min=6))

    def validator(self, form, values):
        if values['current_password'] == values['new_password']:
            exc = colander.Invalid(form)
            exc['new_password'] = _('New password must be different '
                                    'to old password')
            raise exc


@colander.deferred
def deferred_username_validator(node, kw):

    def name_validator(node, value):
        msg = _(
            u'Username may only contain alphanumeric characters '
            u'underscores, periods or dashes and must begin with '
            u'alphanumeric character or underscore')

        if not re.match(r'^[\w]{1}[\w\-\.]{0,254}$', value):
            raise colander.Invalid(node, msg)

    return name_validator


@colander.deferred
def deferred_email_validator(node, kw):
    # NOTE(marcink): we might provide uniqueness validation later here...
    return colander.Email()


class UserSchema(colander.Schema):
    username = colander.SchemaNode(
        colander.String(),
        validator=deferred_username_validator)

    email = colander.SchemaNode(
        colander.String(),
        validator=deferred_email_validator)

    password = colander.SchemaNode(
        colander.String(), missing='')

    first_name = colander.SchemaNode(
        colander.String(), missing='')

    last_name = colander.SchemaNode(
        colander.String(), missing='')

    active = colander.SchemaNode(
        types.StringBooleanType(),
        missing=False)

    admin = colander.SchemaNode(
        types.StringBooleanType(),
        missing=False)

    extern_name = colander.SchemaNode(
        colander.String(), missing='')

    extern_type = colander.SchemaNode(
        colander.String(), missing='')

    def deserialize(self, cstruct):
        """
        Custom deserialize that allows to chain validation, and verify
        permissions, and as last step uniqueness
        """

        appstruct = super(UserSchema, self).deserialize(cstruct)
        return appstruct
