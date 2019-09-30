import collections
# -*- coding: utf-8 -*-

# Copyright (C) 2010-2019 RhodeCode GmbH
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

import pytest

from rhodecode.lib import audit_logger


@pytest.mark.parametrize('store_type', [
    'store_web',
    'store_api'
])
@pytest.mark.parametrize('action, kwargs', [
    ('repo.edit', {
        'user': audit_logger.UserWrap(username='test-audit-log', ip_addr='8.8.8.8'),
        'action_data': {'data': {'hello': 'world'}}
    }),
    ('repo.edit', {
        'user': audit_logger.UserWrap(username=u'marcinkużmiń', ip_addr='8.8.8.8'),
        'action_data': {'data': {'hello': u'ąężą∑ęī¨¨ķ©'}}
    }),
    ('repo.edit', {
        'user': audit_logger.UserWrap(username='marcinkużmiń', ip_addr='8.8.8.8'),
        'action_data': {'data': {'hello': 'ąężą∑ęī¨¨ķ©'}}
    }),
])
def test_store_audit_log(app, store_type, action, kwargs):
    store_action = getattr(audit_logger, store_type)
    store_action(action, **kwargs)
