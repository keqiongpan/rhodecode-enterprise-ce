# -*- coding: utf-8 -*-

# Copyright (C) 2010-2016  RhodeCode GmbH
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
import rhodecode
import rhodecode.lib.vcs.client as client

@pytest.mark.usefixtures('autologin_user', 'app')
def test_vcs_available_returns_summary_page(app, backend):
    url = '/{repo_name}'.format(repo_name=backend.repo.repo_name)
    response = app.get(url)
    assert response.status_code == 200
    assert 'Summary' in response.body


@pytest.mark.usefixtures('autologin_user', 'app')
def test_vcs_unavailable_returns_vcs_error_page(app, backend):
    url = '/{repo_name}'.format(repo_name=backend.repo.repo_name)

    try:
        rhodecode.disable_error_handler = False
        with mock.patch.object(client, '_get_proxy_method') as p:
            p.side_effect = client.exceptions.PyroVCSCommunicationError()
            response = app.get(url, expect_errors=True)
    finally:
        rhodecode.disable_error_handler = True

    assert response.status_code == 502
    assert 'Could not connect to VCS Server' in response.body
