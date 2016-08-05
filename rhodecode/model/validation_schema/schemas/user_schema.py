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

import colander

from rhodecode import forms
from rhodecode.model.db import User
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
