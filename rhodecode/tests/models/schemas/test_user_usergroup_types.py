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

import colander
import pytest

from rhodecode.model import validation_schema
from rhodecode.model.db import Session
from rhodecode.model.user import UserModel
from rhodecode.model.user_group import UserGroupModel
from rhodecode.model.validation_schema.types import (
    UserOrUserGroupType, UserType, UserGroupType
)


class TestUserAndUserGroupSchemaType(object):

    class Schema(colander.Schema):
        user_or_usergroup = colander.SchemaNode(UserOrUserGroupType())

    def test_serialize(self, user_regular, test_user_group):
        schema = self.Schema()

        assert schema.serialize({'user_or_usergroup': user_regular}) == (
            {'user_or_usergroup': 'user:' + user_regular.username})
        assert schema.serialize({'user_or_usergroup': test_user_group}) == (
            {'user_or_usergroup': 'usergroup:' + test_user_group.users_group_name})

        with pytest.raises(colander.Invalid):
            schema.serialize({'user_or_usergroup': 'invalidusername'})

    def test_deserialize(self, test_user_group, user_regular):
        schema = self.Schema()

        assert schema.deserialize(
            {'user_or_usergroup': test_user_group.users_group_name}
        ) == {'user_or_usergroup': test_user_group}

        assert schema.deserialize(
            {'user_or_usergroup': user_regular.username}
        ) == {'user_or_usergroup': user_regular}

    def test_deserialize_user_user_group_with_same_name(self):
        schema = self.Schema()
        try:
            user = UserModel().create_or_update(
                'test_user_usergroup', 'nopass', 'test_user_usergroup')
            usergroup = UserGroupModel().create(
                'test_user_usergroup', 'test usergroup', user)

            with pytest.raises(colander.Invalid) as exc_info:
                schema.deserialize(
                    {'user_or_usergroup': user.username}
                ) == {'user_or_usergroup': user}

            err = exc_info.value.asdict()
            assert 'is both a user and usergroup' in err['user_or_usergroup']
        finally:
            UserGroupModel().delete(usergroup)
            Session().commit()
            UserModel().delete(user)


class TestUserType(object):

    class Schema(colander.Schema):
        user = colander.SchemaNode(UserType())

    def test_serialize(self, user_regular, test_user_group):
        schema = self.Schema()

        assert schema.serialize({'user': user_regular}) == (
            {'user': user_regular.username})

        with pytest.raises(colander.Invalid):
            schema.serialize({'user': test_user_group})

        with pytest.raises(colander.Invalid):
            schema.serialize({'user': 'invaliduser'})

    def test_deserialize(self, user_regular, test_user_group):
        schema = self.Schema()

        assert schema.deserialize(
            {'user': user_regular.username}) == {'user': user_regular}

        with pytest.raises(colander.Invalid):
            schema.deserialize({'user': test_user_group.users_group_name})

        with pytest.raises(colander.Invalid):
            schema.deserialize({'user': 'invaliduser'})


class TestUserGroupType(object):

    class Schema(colander.Schema):
        usergroup = colander.SchemaNode(
            UserGroupType()
        )

    def test_serialize(self, user_regular, test_user_group):
        schema = self.Schema()

        assert schema.serialize({'usergroup': test_user_group}) == (
            {'usergroup': test_user_group.users_group_name})

        with pytest.raises(colander.Invalid):
            schema.serialize({'usergroup': user_regular})

        with pytest.raises(colander.Invalid):
            schema.serialize({'usergroup': 'invalidusergroup'})

    def test_deserialize(self, user_regular, test_user_group):
        schema = self.Schema()

        assert schema.deserialize({
            'usergroup': test_user_group.users_group_name
        }) == {'usergroup': test_user_group}

        with pytest.raises(colander.Invalid):
            schema.deserialize({'usergroup': user_regular.username})

        with pytest.raises(colander.Invalid):
            schema.deserialize({'usergroup': 'invaliduser'})
