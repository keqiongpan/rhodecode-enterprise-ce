# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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
from rhodecode.model.db import Repository


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'pullrequest_show_all': '/{repo_name}/pull-request',
        'pullrequest_show_all_data': '/{repo_name}/pull-request-data',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


@pytest.mark.backends("git", "hg")
@pytest.mark.usefixtures('autologin_user', 'app')
class TestPullRequestList(object):

    @pytest.mark.parametrize('params, expected_title', [
        ({'source': 0, 'closed': 1}, 'Closed'),
        ({'source': 0, 'my': 1}, 'Created by me'),
        ({'source': 0, 'awaiting_review': 1}, 'Awaiting review'),
        ({'source': 0, 'awaiting_my_review': 1}, 'Awaiting my review'),
        ({'source': 1}, 'From this repo'),
    ])
    def test_showing_list_page(self, backend, pr_util, params, expected_title):
        pull_request = pr_util.create_pull_request()

        response = self.app.get(
            route_path('pullrequest_show_all',
                       repo_name=pull_request.target_repo.repo_name,
                       params=params))

        assert_response = response.assert_response()

        element = assert_response.get_element('.title .active')
        element_text = element.text_content()
        assert expected_title == element_text

    def test_showing_list_page_data(self, backend, pr_util, xhr_header):
        pull_request = pr_util.create_pull_request()
        response = self.app.get(
            route_path('pullrequest_show_all_data',
                       repo_name=pull_request.target_repo.repo_name),
            extra_environ=xhr_header)

        assert response.json['recordsTotal'] == 1
        assert response.json['data'][0]['description'] == 'Description'

    def test_description_is_escaped_on_index_page(self, backend, pr_util, xhr_header):
        xss_description = "<script>alert('Hi!')</script>"
        pull_request = pr_util.create_pull_request(description=xss_description)

        response = self.app.get(
            route_path('pullrequest_show_all_data',
                       repo_name=pull_request.target_repo.repo_name),
            extra_environ=xhr_header)

        assert response.json['recordsTotal'] == 1
        assert response.json['data'][0]['description'] == \
               "&lt;script&gt;alert(&#39;Hi!&#39;)&lt;/script&gt;"
