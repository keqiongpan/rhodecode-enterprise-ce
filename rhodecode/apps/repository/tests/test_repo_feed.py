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
from rhodecode.model.auth_token import AuthTokenModel
from rhodecode.tests import TestController


def route_path(name, params=None, **kwargs):
    import urllib

    base_url = {
        'rss_feed_home': '/{repo_name}/feed/rss',
        'atom_feed_home': '/{repo_name}/feed/atom',
    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestFeedView(TestController):

    @pytest.mark.parametrize("feed_type,response_types,content_type",[
        ('rss', ['<rss version="2.0">'],
         "application/rss+xml"),
        ('atom', ['xmlns="http://www.w3.org/2005/Atom"', 'xml:lang="en-us"'],
         "application/atom+xml"),
    ])
    def test_feed(self, backend, feed_type, response_types, content_type):
        self.log_user()
        response = self.app.get(
            route_path('{}_feed_home'.format(feed_type),
                       repo_name=backend.repo_name))

        for content in response_types:
            response.mustcontain(content)

        assert response.content_type == content_type

    @pytest.mark.parametrize("feed_type, content_type", [
        ('rss', "application/rss+xml"),
        ('atom', "application/atom+xml")
    ])
    def test_feed_with_auth_token(
            self, backend, user_admin, feed_type, content_type):
        auth_token = user_admin.feed_token
        assert auth_token != ''

        response = self.app.get(
            route_path(
                '{}_feed_home'.format(feed_type),
                repo_name=backend.repo_name,
                params=dict(auth_token=auth_token)),
            status=200)

        assert response.content_type == content_type

    @pytest.mark.parametrize("feed_type", ['rss', 'atom'])
    def test_feed_with_auth_token_of_wrong_type(
            self, backend, user_util, feed_type):
        user = user_util.create_user()
        auth_token = AuthTokenModel().create(
            user.user_id, 'test-token', -1, AuthTokenModel.cls.ROLE_API)
        auth_token = auth_token.api_key

        self.app.get(
            route_path(
                '{}_feed_home'.format(feed_type),
                repo_name=backend.repo_name,
                params=dict(auth_token=auth_token)),
            status=302)

        auth_token = AuthTokenModel().create(
            user.user_id, 'test-token', -1, AuthTokenModel.cls.ROLE_FEED)
        auth_token = auth_token.api_key
        self.app.get(
            route_path(
                '{}_feed_home'.format(feed_type),
                repo_name=backend.repo_name,
                params=dict(auth_token=auth_token)),
            status=200)
