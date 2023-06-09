# -*- coding: utf-8 -*-

# Copyright (C) 2012-2020 RhodeCode GmbH
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
from pyramid import compat

from rhodecode.config.utils import set_instance_id


@pytest.mark.parametrize('instance_id', ['', None, '*', 'custom-id'])
def test_set_instance_id(instance_id):
    config = {'instance_id': instance_id}
    set_instance_id(config)

    if instance_id == 'custom-id':
        assert config['instance_id'] == instance_id
    else:
        assert isinstance(config['instance_id'], compat.string_types)
        assert len(config['instance_id'])
        assert instance_id != config['instance_id']
