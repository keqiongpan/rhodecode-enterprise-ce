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


import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


@connection_available
@pytest.mark.parametrize('link_data', routing_links.link_config)
def test_connect_redirection_links(link_data):
    response = requests_retry_session().get(link_data['target'])
    if link_data['name'] == 'enterprise_license_convert_from_old':
        # special case for a page that requires a valid login
        assert response.url == 'https://rhodecode.com/login'
    else:
        assert response.url == link_data['external_target']
