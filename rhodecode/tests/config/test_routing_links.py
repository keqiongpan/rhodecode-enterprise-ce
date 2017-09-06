# -*- coding: utf-8 -*-

# Copyright (C) 2010-2017 RhodeCode GmbH
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
import requests
from rhodecode.config import routing_links


def check_connection():
    try:
        response = requests.get('https://rhodecode.com')
        return response.status_code == 200
    except Exception as e:
        print(e)

    return False


connection_available = pytest.mark.skipif(
    not check_connection(), reason="No outside internet connection available")


@connection_available
def test_connect_redirection_links():

    for link_data in routing_links.link_config:
        response = requests.get(link_data['target'])
        if link_data['name'] == 'enterprise_license_convert_from_old':
            # special case for a page that requires a valid login
            assert response.url == 'https://rhodecode.com/login'
        else:
            assert response.url == link_data['external_target']
