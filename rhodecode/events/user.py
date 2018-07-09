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
import logging

from zope.interface import implementer

from rhodecode.translation import lazy_ugettext
from rhodecode.events.base import RhodecodeEvent
from rhodecode.events.interfaces import (
    IUserRegistered, IUserPreCreate, IUserPreUpdate)

log = logging.getLogger(__name__)


@implementer(IUserRegistered)
class UserRegistered(RhodecodeEvent):
    """
    An instance of this class is emitted as an :term:`event` whenever a user
    account is registered.
    """
    name = 'user-register'
    display_name = lazy_ugettext('user registered')

    def __init__(self, user, session):
        super(UserRegistered, self).__init__()
        self.user = user
        self.session = session


@implementer(IUserPreCreate)
class UserPreCreate(RhodecodeEvent):
    """
    An instance of this class is emitted as an :term:`event` before a new user
    object is created.
    """
    name = 'user-pre-create'
    display_name = lazy_ugettext('user pre create')

    def __init__(self, user_data):
        super(UserPreCreate, self).__init__()
        self.user_data = user_data


@implementer(IUserPreCreate)
class UserPostCreate(RhodecodeEvent):
    """
    An instance of this class is emitted as an :term:`event` after a new user
    object is created.
    """
    name = 'user-post-create'
    display_name = lazy_ugettext('user post create')

    def __init__(self, user_data):
        super(UserPostCreate, self).__init__()
        self.user_data = user_data


@implementer(IUserPreUpdate)
class UserPreUpdate(RhodecodeEvent):
    """
    An instance of this class is emitted as an :term:`event` before a user
    object is updated.
    """
    name = 'user-pre-update'
    display_name = lazy_ugettext('user pre update')

    def __init__(self, user, user_data):
        super(UserPreUpdate, self).__init__()
        self.user = user
        self.user_data = user_data


class UserPermissionsChange(RhodecodeEvent):
    """
    This event should be triggered on an event that permissions of user might changed.
    Currently this should be triggered on:

      - user added/removed from user group
      - repo permissions changed
      - repo group permissions changed
      - user group permissions changed

    """
    name = 'user-permissions-change'
    display_name = lazy_ugettext('user permissions change')

    def __init__(self, user_ids):
        super(UserPermissionsChange, self).__init__()
        self.user_ids = user_ids
