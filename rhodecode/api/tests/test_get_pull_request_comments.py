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
import urlobject

from rhodecode.api.tests.utils import (
    build_data, api_call, assert_error, assert_ok)
from rhodecode.lib import helpers as h
from rhodecode.lib.utils2 import safe_unicode

pytestmark = pytest.mark.backends("git", "hg")


@pytest.mark.usefixtures("testuser_api", "app")
class TestGetPullRequestComments(object):

    def test_api_get_pull_request_comments(self, pr_util, http_host_only_stub):
        from rhodecode.model.pull_request import PullRequestModel

        pull_request = pr_util.create_pull_request(mergeable=True)
        id_, params = build_data(
            self.apikey, 'get_pull_request_comments',
            pullrequestid=pull_request.pull_request_id)

        response = api_call(self.app, params)

        assert response.status == '200 OK'
        resp_date = response.json['result'][0]['comment_created_on']
        resp_comment_id = response.json['result'][0]['comment_id']

        expected = [
            {'comment_author': {'active': True,
                                'full_name_or_username': 'RhodeCode Admin',
                                'username': 'test_admin'},
             'comment_created_on': resp_date,
             'comment_f_path': None,
             'comment_id': resp_comment_id,
             'comment_lineno': None,
             'comment_status': {'status': 'under_review',
                                'status_lbl': 'Under Review'},
             'comment_text': 'Auto status change to |new_status|\n\n.. |new_status| replace:: *"Under Review"*',
             'comment_type': 'note',
             'comment_resolved_by': None,
             'pull_request_version': None,
             'comment_last_version': 0,
             'comment_commit_id': None,
             'comment_pull_request_id': pull_request.pull_request_id
             }
        ]
        assert_ok(id_, expected, response.body)

    def test_api_get_pull_request_comments_repo_error(self, pr_util):
        pull_request = pr_util.create_pull_request()
        id_, params = build_data(
            self.apikey, 'get_pull_request_comments',
            repoid=666, pullrequestid=pull_request.pull_request_id)
        response = api_call(self.app, params)

        expected = 'repository `666` does not exist'
        assert_error(id_, expected, given=response.body)

    def test_api_get_pull_request_comments_pull_request_error(self):
        id_, params = build_data(
            self.apikey, 'get_pull_request_comments', pullrequestid=666)
        response = api_call(self.app, params)

        expected = 'pull request `666` does not exist'
        assert_error(id_, expected, given=response.body)
