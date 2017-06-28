# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 RhodeCode GmbH
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


from rhodecode.apps._base import ADMIN_PREFIX


def includeme(config):

    config.add_route(
        name='my_account_profile',
        pattern=ADMIN_PREFIX + '/my_account/profile')

    config.add_route(
        name='my_account_password',
        pattern=ADMIN_PREFIX + '/my_account/password')

    config.add_route(
        name='my_account_password_update',
        pattern=ADMIN_PREFIX + '/my_account/password')

    config.add_route(
        name='my_account_auth_tokens',
        pattern=ADMIN_PREFIX + '/my_account/auth_tokens')
    config.add_route(
        name='my_account_auth_tokens_add',
        pattern=ADMIN_PREFIX + '/my_account/auth_tokens/new')
    config.add_route(
        name='my_account_auth_tokens_delete',
        pattern=ADMIN_PREFIX + '/my_account/auth_tokens/delete')

    config.add_route(
        name='my_account_emails',
        pattern=ADMIN_PREFIX + '/my_account/emails')
    config.add_route(
        name='my_account_emails_add',
        pattern=ADMIN_PREFIX + '/my_account/emails/new')
    config.add_route(
        name='my_account_emails_delete',
        pattern=ADMIN_PREFIX + '/my_account/emails/delete')

    config.add_route(
        name='my_account_repos',
        pattern=ADMIN_PREFIX + '/my_account/repos')

    config.add_route(
        name='my_account_watched',
        pattern=ADMIN_PREFIX + '/my_account/watched')

    config.add_route(
        name='my_account_perms',
        pattern=ADMIN_PREFIX + '/my_account/perms')

    config.add_route(
        name='my_account_notifications',
        pattern=ADMIN_PREFIX + '/my_account/notifications')

    config.add_route(
        name='my_account_notifications_toggle_visibility',
        pattern=ADMIN_PREFIX + '/my_account/toggle_visibility')

    # channelstream test
    config.add_route(
        name='my_account_notifications_test_channelstream',
        pattern=ADMIN_PREFIX + '/my_account/test_channelstream')

    # Scan module for configuration decorators.
    config.scan()
