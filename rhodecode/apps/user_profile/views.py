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
from rhodecode.lib.auth import LoginRequired, NotAnonymous

from rhodecode.model.db import User
from rhodecode.model.user import UserModel

log = logging.getLogger(__name__)


class UserProfileView(BaseAppView):

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='user_profile', request_method='GET',
        renderer='rhodecode:templates/users/user.mako')
    def user_profile(self):
        # register local template context
        c = self._get_local_tmpl_context()
        c.active = 'user_profile'

        username = self.request.matchdict.get('username')

        c.user = UserModel().get_by_username(username)
        if not c.user or c.user.username == User.DEFAULT_USER:
            raise HTTPNotFound()

        return self._get_template_context(c)
