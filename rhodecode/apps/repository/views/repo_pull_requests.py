# -*- coding: utf-8 -*-

# Copyright (C) 2011-2017 RhodeCode GmbH
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

import logging

from pyramid.view import view_config

from rhodecode.apps._base import RepoAppView, DataGridAppView
from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator)
from rhodecode.lib.utils import PartialRenderer
from rhodecode.lib.utils2 import str2bool
from rhodecode.model.comment import CommentsModel
from rhodecode.model.db import PullRequest
from rhodecode.model.pull_request import PullRequestModel

log = logging.getLogger(__name__)


class RepoPullRequestsView(RepoAppView, DataGridAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()

        # TODO(marcink): remove repo_info and use c.rhodecode_db_repo instead
        c.repo_info = self.db_repo

        self._register_global_c(c)
        return c

    def _get_pull_requests_list(
            self, repo_name, source, filter_type, opened_by, statuses):

        draw, start, limit = self._extract_chunk(self.request)
        search_q, order_by, order_dir = self._extract_ordering(self.request)
        _render = PartialRenderer('data_table/_dt_elements.mako')

        # pagination

        if filter_type == 'awaiting_review':
            pull_requests = PullRequestModel().get_awaiting_review(
                repo_name, source=source, opened_by=opened_by,
                statuses=statuses, offset=start, length=limit,
                order_by=order_by, order_dir=order_dir)
            pull_requests_total_count = PullRequestModel().count_awaiting_review(
                repo_name, source=source, statuses=statuses,
                opened_by=opened_by)
        elif filter_type == 'awaiting_my_review':
            pull_requests = PullRequestModel().get_awaiting_my_review(
                repo_name, source=source, opened_by=opened_by,
                user_id=self._rhodecode_user.user_id, statuses=statuses,
                offset=start, length=limit, order_by=order_by,
                order_dir=order_dir)
            pull_requests_total_count = PullRequestModel().count_awaiting_my_review(
                repo_name, source=source, user_id=self._rhodecode_user.user_id,
                statuses=statuses, opened_by=opened_by)
        else:
            pull_requests = PullRequestModel().get_all(
                repo_name, source=source, opened_by=opened_by,
                statuses=statuses, offset=start, length=limit,
                order_by=order_by, order_dir=order_dir)
            pull_requests_total_count = PullRequestModel().count_all(
                repo_name, source=source, statuses=statuses,
                opened_by=opened_by)

        data = []
        comments_model = CommentsModel()
        for pr in pull_requests:
            comments = comments_model.get_all_comments(
                self.db_repo.repo_id, pull_request=pr)

            data.append({
                'name': _render('pullrequest_name',
                                pr.pull_request_id, pr.target_repo.repo_name),
                'name_raw': pr.pull_request_id,
                'status': _render('pullrequest_status',
                                  pr.calculated_review_status()),
                'title': _render(
                    'pullrequest_title', pr.title, pr.description),
                'description': h.escape(pr.description),
                'updated_on': _render('pullrequest_updated_on',
                                      h.datetime_to_time(pr.updated_on)),
                'updated_on_raw': h.datetime_to_time(pr.updated_on),
                'created_on': _render('pullrequest_updated_on',
                                      h.datetime_to_time(pr.created_on)),
                'created_on_raw': h.datetime_to_time(pr.created_on),
                'author': _render('pullrequest_author',
                                  pr.author.full_contact, ),
                'author_raw': pr.author.full_name,
                'comments': _render('pullrequest_comments', len(comments)),
                'comments_raw': len(comments),
                'closed': pr.is_closed(),
            })

        data = ({
            'draw': draw,
            'data': data,
            'recordsTotal': pull_requests_total_count,
            'recordsFiltered': pull_requests_total_count,
        })
        return data

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='pullrequest_show_all', request_method='GET',
        renderer='rhodecode:templates/pullrequests/pullrequests.mako')
    def pull_request_list(self):
        c = self.load_default_context()

        req_get = self.request.GET
        c.source = str2bool(req_get.get('source'))
        c.closed = str2bool(req_get.get('closed'))
        c.my = str2bool(req_get.get('my'))
        c.awaiting_review = str2bool(req_get.get('awaiting_review'))
        c.awaiting_my_review = str2bool(req_get.get('awaiting_my_review'))

        c.active = 'open'
        if c.my:
            c.active = 'my'
        if c.closed:
            c.active = 'closed'
        if c.awaiting_review and not c.source:
            c.active = 'awaiting'
        if c.source and not c.awaiting_review:
            c.active = 'source'
        if c.awaiting_my_review:
            c.active = 'awaiting_my'

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='pullrequest_show_all_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def pull_request_list_data(self):

        # additional filters
        req_get = self.request.GET
        source = str2bool(req_get.get('source'))
        closed = str2bool(req_get.get('closed'))
        my = str2bool(req_get.get('my'))
        awaiting_review = str2bool(req_get.get('awaiting_review'))
        awaiting_my_review = str2bool(req_get.get('awaiting_my_review'))

        filter_type = 'awaiting_review' if awaiting_review \
            else 'awaiting_my_review' if awaiting_my_review \
            else None

        opened_by = None
        if my:
            opened_by = [self._rhodecode_user.user_id]

        statuses = [PullRequest.STATUS_NEW, PullRequest.STATUS_OPEN]
        if closed:
            statuses = [PullRequest.STATUS_CLOSED]

        data = self._get_pull_requests_list(
            repo_name=self.db_repo_name, source=source,
            filter_type=filter_type, opened_by=opened_by, statuses=statuses)

        return data
