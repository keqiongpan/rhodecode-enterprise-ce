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
        name='my_account_auth_tokens',
        pattern=ADMIN_PREFIX + '/my_account/auth_tokens')
    config.add_route(
        name='my_account_auth_tokens_add',
        pattern=ADMIN_PREFIX + '/my_account/auth_tokens/new',
        )
    config.add_route(
        name='my_account_auth_tokens_delete',
        pattern=ADMIN_PREFIX + '/my_account/auth_tokens/delete',
        )

    # Scan module for configuration decorators.
    config.scan()
