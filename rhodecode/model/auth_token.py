# -*- coding: utf-8 -*-

# Copyright (C) 2013-2020 RhodeCode GmbH
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

"""
authentication tokens model for RhodeCode
"""

import time
import logging
import traceback
from sqlalchemy import or_

from rhodecode.model import BaseModel
from rhodecode.model.db import UserApiKeys
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


class AuthTokenModel(BaseModel):
    cls = UserApiKeys

    @classmethod
    def get_lifetime_values(cls, translator):
        from rhodecode.lib import helpers as h
        _ = translator

        def date_after_min(mins):
            after = time.time() + (60 * mins)
            return h.format_date(h.time_to_datetime(after))

        return [
            (str(-1),
             _('forever')),
            (str(5),
             _('5 minutes {end_date}').format(end_date=date_after_min(5))),
            (str(60),
             _('1 hour {end_date}').format(end_date=date_after_min(60))),
            (str(60 * 24),
             _('1 day {end_date}').format(end_date=date_after_min(60 * 24))),
            (str(60 * 24 * 30),
             _('1 month {end_date}').format(end_date=date_after_min(60 * 24 * 30))),
        ]

    def create(self, user, description, lifetime=-1, role=UserApiKeys.ROLE_ALL):
        """
        :param user: user or user_id
        :param description: description of ApiKey
        :param lifetime: expiration time in minutes
        :param role: role for the apikey
        """
        from rhodecode.lib.auth import generate_auth_token

        user = self._get_user(user)

        new_auth_token = UserApiKeys()
        new_auth_token.api_key = generate_auth_token(user.username)
        new_auth_token.user_id = user.user_id
        new_auth_token.description = description
        new_auth_token.role = role
        new_auth_token.expires = time.time() + (lifetime * 60) \
            if lifetime != -1 else -1
        Session().add(new_auth_token)

        return new_auth_token

    def delete(self, auth_token_id, user=None):
        """
        Deletes given api_key, if user is set it also filters the object for
        deletion by given user.
        """
        auth_token = UserApiKeys.query().filter(
            UserApiKeys.user_api_key_id == auth_token_id)

        if user:
            user = self._get_user(user)
            auth_token = auth_token.filter(UserApiKeys.user_id == user.user_id)
            auth_token = auth_token.scalar()

        if auth_token:
            try:
                Session().delete(auth_token)
            except Exception:
                log.error(traceback.format_exc())
                raise

    def get_auth_tokens(self, user, show_expired=True):
        user = self._get_user(user)
        user_auth_tokens = UserApiKeys.query()\
            .filter(UserApiKeys.user_id == user.user_id)
        if not show_expired:
            user_auth_tokens = user_auth_tokens\
                .filter(or_(UserApiKeys.expires == -1,
                            UserApiKeys.expires >= time.time()))
        user_auth_tokens = user_auth_tokens.order_by(
            UserApiKeys.user_api_key_id)
        return user_auth_tokens

    def get_auth_token(self, auth_token):
        auth_token = UserApiKeys.query().filter(
            UserApiKeys.api_key == auth_token)
        auth_token = auth_token \
            .filter(or_(UserApiKeys.expires == -1,
                        UserApiKeys.expires >= time.time()))\
            .first()

        return auth_token
