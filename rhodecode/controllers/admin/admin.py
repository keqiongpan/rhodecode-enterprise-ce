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

"""
Controller for Admin panel of RhodeCode Enterprise
"""


import logging

from pylons import request, tmpl_context as c, url
from pylons.controllers.util import redirect
from sqlalchemy.orm import joinedload

from rhodecode.model.db import UserLog, PullRequest
from rhodecode.lib.user_log_filter import user_log_filter
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.utils2 import safe_int
from rhodecode.lib.helpers import Page


log = logging.getLogger(__name__)


class AdminController(BaseController):

    @LoginRequired()
    def __before__(self):
        super(AdminController, self).__before__()

    @HasPermissionAllDecorator('hg.admin')
    def index(self):
        users_log = UserLog.query()\
            .options(joinedload(UserLog.user))\
            .options(joinedload(UserLog.repository))

        # FILTERING
        c.search_term = request.GET.get('filter')
        try:
            users_log = user_log_filter(users_log, c.search_term)
        except Exception:
            # we want this to crash for now
            raise

        users_log = users_log.order_by(UserLog.action_date.desc())

        p = safe_int(request.GET.get('page', 1), 1)

        def url_generator(**kw):
            return url.current(filter=c.search_term, **kw)

        c.audit_logs = Page(users_log, page=p, items_per_page=10,
                           url=url_generator)
        c.log_data = render('admin/admin_log.mako')

        if request.is_xhr:
            return c.log_data
        return render('admin/admin.mako')

    # global redirect doesn't need permissions
    def pull_requests(self, pull_request_id):
        """
        Global redirect for Pull Requests

        :param pull_request_id: id of pull requests in the system
        """
        pull_request = PullRequest.get_or_404(pull_request_id)
        repo_name = pull_request.target_repo.repo_name
        return redirect(url(
            'pullrequest_show', repo_name=repo_name,
            pull_request_id=pull_request_id))
