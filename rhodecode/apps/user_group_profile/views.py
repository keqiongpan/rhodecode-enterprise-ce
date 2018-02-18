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

import logging

from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config

from rhodecode.apps._base import BaseAppView
from rhodecode.lib.auth import HasUserGroupPermissionAnyDecorator, LoginRequired, NotAnonymous
from rhodecode.model.db import UserGroup, User


log = logging.getLogger(__name__)


class UserGroupProfileView(BaseAppView):

    @LoginRequired()
    @NotAnonymous()
    @HasUserGroupPermissionAnyDecorator('usergroup.read', 'usergroup.write', 'usergroup.admin',)
    @view_config(
        route_name='user_group_profile', request_method='GET',
        renderer='rhodecode:templates/user_group/user_group.mako')
    def user_group_profile(self):
        c = self._get_local_tmpl_context()
        c.active = 'profile'
        self.db_user_group_name = self.request.matchdict.get('user_group_name')
        c.user_group = UserGroup().get_by_group_name(self.db_user_group_name)
        if not c.user_group:
            raise HTTPNotFound()
        group_members_obj = sorted((x.user for x in c.user_group.members),
                                   key=lambda u: u.username.lower())
        c.group_members = group_members_obj
        c.anonymous = self._rhodecode_user.username == User.DEFAULT_USER
        return self._get_template_context(c)
