# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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


import mock
import pytest

from rhodecode.config import environment


@pytest.fixture
def _external_calls_patcher(request):
    # TODO: mikhail: This is a temporary solution. Ideally load_environment
    # should be split into multiple small testable functions.
    utils_patcher = mock.patch.object(environment, 'utils')

    rhodecode_patcher = mock.patch.object(environment, 'rhodecode')

    db_config = mock.Mock()
    db_config.items.return_value = {
        'paths': [['/tmp/abc', '/tmp/def']]
    }
    db_config_patcher = mock.patch.object(
        environment, 'make_db_config', return_value=db_config)

    set_config_patcher = mock.patch.object(environment, 'set_rhodecode_config')

    utils_patcher.start()
    rhodecode_patcher.start()
    db_config_patcher.start()
    set_config_patcher.start()

    request.addfinalizer(utils_patcher.stop)
    request.addfinalizer(rhodecode_patcher.stop)
    request.addfinalizer(db_config_patcher.stop)
    request.addfinalizer(set_config_patcher.stop)
