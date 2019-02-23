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

import colander
import pytest

from rhodecode.model import validation_schema
from rhodecode.model.validation_schema.schemas import user_schema


class TestChangePasswordSchema(object):
    original_password = 'm092d903fnio0m'

    def test_deserialize_bad_data(self, user_regular):
        schema = user_schema.ChangePasswordSchema().bind(
            username=user_regular.username)

        with pytest.raises(validation_schema.Invalid) as exc_info:
            schema.deserialize('err')
        err = exc_info.value.asdict()
        assert err[''] == '"err" is not a mapping type: ' \
                          'Does not implement dict-like functionality.'

    def test_validate_valid_change_password_data(self, user_util):
        user = user_util.create_user(password=self.original_password)
        schema = user_schema.ChangePasswordSchema().bind(
            username=user.username)

        schema.deserialize({
            'current_password': self.original_password,
            'new_password': '23jf04rm04imr'
        })

    @pytest.mark.parametrize(
        'current_password,new_password,key,message', [
        ('', 'abcdef123', 'current_password', 'required'),
        ('wrong_pw', 'abcdef123', 'current_password', 'incorrect'),
        (original_password, original_password, 'new_password', 'different'),
        (original_password, '', 'new_password', 'Required'),
        (original_password, 'short', 'new_password', 'minimum'),
    ])
    def test_validate_invalid_change_password_data(self, current_password,
                                                   new_password, key, message,
                                                   user_util):
        user = user_util.create_user(password=self.original_password)
        schema = user_schema.ChangePasswordSchema().bind(
            username=user.username)

        with pytest.raises(validation_schema.Invalid) as exc_info:
            schema.deserialize({
                'current_password': current_password,
                'new_password': new_password
            })
        err = exc_info.value.asdict()
        assert message.lower() in err[key].lower()
