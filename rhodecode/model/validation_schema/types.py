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

import re

import colander
from pyramid import compat

from rhodecode.model.validation_schema import preparers
from rhodecode.model.db import User, UserGroup


class _RootLocation(object):
    pass

RootLocation = _RootLocation()


def _normalize(seperator, path):

    if not path:
        return ''
    elif path is colander.null:
        return colander.null

    parts = path.split(seperator)

    def bad_parts(value):
        if not value:
            return False
        if re.match(r'^[.]+$', value):
            return False

        return True

    def slugify(value):
        value = preparers.slugify_preparer(value)
        value = re.sub(r'[.]{2,}', '.', value)
        return value

    clean_parts = [slugify(item) for item in parts if item]
    path = filter(bad_parts, clean_parts)
    return seperator.join(path)


class RepoNameType(colander.String):
    SEPARATOR = '/'

    def deserialize(self, node, cstruct):
        result = super(RepoNameType, self).deserialize(node, cstruct)
        if cstruct is colander.null:
            return colander.null
        return self._normalize(result)

    def _normalize(self, path):
        return _normalize(self.SEPARATOR, path)


class GroupNameType(colander.String):
    SEPARATOR = '/'

    def deserialize(self, node, cstruct):
        if cstruct is RootLocation:
            return cstruct

        result = super(GroupNameType, self).deserialize(node, cstruct)
        if cstruct is colander.null:
            return colander.null
        return self._normalize(result)

    def _normalize(self, path):
        return _normalize(self.SEPARATOR, path)


class StringBooleanType(colander.String):
    true_values = ['true', 't', 'yes', 'y', 'on', '1']
    false_values = ['false', 'f', 'no', 'n', 'off', '0']

    def serialize(self, node, appstruct):
        if appstruct is colander.null:
            return colander.null
        if not isinstance(appstruct, bool):
            raise colander.Invalid(node, '%r is not a boolean' % appstruct)

        return appstruct and 'true' or 'false'

    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return colander.null

        if isinstance(cstruct, bool):
            return cstruct

        if not isinstance(cstruct, compat.string_types):
            raise colander.Invalid(node, '%r is not a string' % cstruct)

        value = cstruct.lower()
        if value in self.true_values:
            return True
        elif value in self.false_values:
            return False
        else:
            raise colander.Invalid(
                node, '{} value cannot be translated to bool'.format(value))


class UserOrUserGroupType(colander.SchemaType):
    """ colander Schema type for valid rhodecode user and/or usergroup """
    scopes = ('user', 'usergroup')

    def __init__(self):
        self.users = 'user' in self.scopes
        self.usergroups = 'usergroup' in self.scopes

    def serialize(self, node, appstruct):
        if appstruct is colander.null:
            return colander.null

        if self.users:
            if isinstance(appstruct, User):
                if self.usergroups:
                    return 'user:%s' % appstruct.username
                return appstruct.username

        if self.usergroups:
            if isinstance(appstruct, UserGroup):
                if self.users:
                    return 'usergroup:%s' % appstruct.users_group_name
                return appstruct.users_group_name

        raise colander.Invalid(
            node, '%s is not a valid %s' % (appstruct, ' or '.join(self.scopes)))

    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return colander.null

        user, usergroup = None, None
        if self.users:
            if cstruct.startswith('user:'):
                user = User.get_by_username(cstruct.split(':')[1])
            else:
                user = User.get_by_username(cstruct)

        if self.usergroups:
            if cstruct.startswith('usergroup:'):
                usergroup = UserGroup.get_by_group_name(cstruct.split(':')[1])
            else:
                usergroup = UserGroup.get_by_group_name(cstruct)

        if self.users and self.usergroups:
            if user and usergroup:
                raise colander.Invalid(node, (
                    '%s is both a user and usergroup, specify which '
                    'one was wanted by prepending user: or usergroup: to the '
                    'name') % cstruct)

        if self.users and user:
            return user

        if self.usergroups and usergroup:
            return usergroup

        raise colander.Invalid(
            node, '%s is not a valid %s' % (cstruct, ' or '.join(self.scopes)))


class UserType(UserOrUserGroupType):
    scopes = ('user',)


class UserGroupType(UserOrUserGroupType):
    scopes = ('usergroup',)


class StrOrIntType(colander.String):
    def deserialize(self, node, cstruct):
        if isinstance(cstruct, compat.string_types):
            return super(StrOrIntType, self).deserialize(node, cstruct)
        else:
            return colander.Integer().deserialize(node, cstruct)
