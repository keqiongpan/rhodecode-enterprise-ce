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
import urlobject

from rhodecode.api.tests.utils import (
    build_data, api_call, assert_error, assert_ok)
from rhodecode.lib import helpers as h
from rhodecode.lib.utils2 import safe_unicode

pytestmark = pytest.mark.backends("git", "hg")


@pytest.mark.usefixtures("testuser_api", "app")
class TestGetPullRequest(object):

    def test_api_get_pull_request(self, pr_util, http_host_only_stub):
        from rhodecode.model.pull_request import PullRequestModel
        pull_request = pr_util.create_pull_request(mergeable=True)
        id_, params = build_data(
            self.apikey, 'get_pull_request',
            pullrequestid=pull_request.pull_request_id)

        response = api_call(self.app, params)

        assert response.status == '200 OK'

        url_obj = urlobject.URLObject(
            h.route_url(
                'pullrequest_show',
                repo_name=pull_request.target_repo.repo_name,
                pull_request_id=pull_request.pull_request_id))

        pr_url = safe_unicode(
            url_obj.with_netloc(http_host_only_stub))
        source_url = safe_unicode(
            pull_request.source_repo.clone_url().with_netloc(http_host_only_stub))
        target_url = safe_unicode(
            pull_request.target_repo.clone_url().with_netloc(http_host_only_stub))
        shadow_url = safe_unicode(
            PullRequestModel().get_shadow_clone_url(pull_request))

        expected = {
            'pull_request_id': pull_request.pull_request_id,
            'url': pr_url,
            'title': pull_request.title,
            'description': pull_request.description,
            'status': pull_request.status,
            'state': pull_request.pull_request_state,
            'created_on': pull_request.created_on,
            'updated_on': pull_request.updated_on,
            'commit_ids': pull_request.revisions,
            'review_status': pull_request.calculated_review_status(),
            'mergeable': {
                'status': True,
                'message': 'This pull request can be automatically merged.',
            },
            'source': {
                'clone_url': source_url,
                'repository': pull_request.source_repo.repo_name,
                'reference': {
                    'name': pull_request.source_ref_parts.name,
                    'type': pull_request.source_ref_parts.type,
                    'commit_id': pull_request.source_ref_parts.commit_id,
                },
            },
            'target': {
                'clone_url': target_url,
                'repository': pull_request.target_repo.repo_name,
                'reference': {
                    'name': pull_request.target_ref_parts.name,
                    'type': pull_request.target_ref_parts.type,
                    'commit_id': pull_request.target_ref_parts.commit_id,
                },
            },
            'merge': {
                'clone_url': shadow_url,
                'reference': {
                    'name': pull_request.shadow_merge_ref.name,
                    'type': pull_request.shadow_merge_ref.type,
                    'commit_id': pull_request.shadow_merge_ref.commit_id,
                },
            },
            'author': pull_request.author.get_api_data(include_secrets=False,
                                                       details='basic'),
            'reviewers': [
                {
                    'user': reviewer.get_api_data(include_secrets=False,
                                                  details='basic'),
                    'reasons': reasons,
                    'review_status': st[0][1].status if st else 'not_reviewed',
                }
                for obj, reviewer, reasons, mandatory, st in
                pull_request.reviewers_statuses()
            ]
        }
        assert_ok(id_, expected, response.body)

    def test_api_get_pull_request_repo_error(self, pr_util):
        pull_request = pr_util.create_pull_request()
        id_, params = build_data(
            self.apikey, 'get_pull_request',
            repoid=666, pullrequestid=pull_request.pull_request_id)
        response = api_call(self.app, params)

        expected = 'repository `666` does not exist'
        assert_error(id_, expected, given=response.body)

    def test_api_get_pull_request_pull_request_error(self):
        id_, params = build_data(
            self.apikey, 'get_pull_request', pullrequestid=666)
        response = api_call(self.app, params)

        expected = 'pull request `666` does not exist'
        assert_error(id_, expected, given=response.body)

    def test_api_get_pull_request_pull_request_error_just_pr_id(self):
        id_, params = build_data(
            self.apikey, 'get_pull_request',
            pullrequestid=666)
        response = api_call(self.app, params)

        expected = 'pull request `666` does not exist'
        assert_error(id_, expected, given=response.body)
