# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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

from pyramid.httpexceptions import HTTPNotFound

from rhodecode.apps._base import BaseAppView
from rhodecode.model.db import joinedload, UserLog
from rhodecode.lib.user_log_filter import user_log_filter
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator
from rhodecode.lib.utils2 import safe_int
from rhodecode.lib.helpers import SqlPage

log = logging.getLogger(__name__)


class AdminAuditLogsView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def admin_audit_logs(self):
        c = self.load_default_context()

        users_log = UserLog.query()\
            .options(joinedload(UserLog.user))\
            .options(joinedload(UserLog.repository))

        # FILTERING
        c.search_term = self.request.GET.get('filter')
        try:
            users_log = user_log_filter(users_log, c.search_term)
        except Exception:
            # we want this to crash for now
            raise

        users_log = users_log.order_by(UserLog.action_date.desc())

        p = safe_int(self.request.GET.get('page', 1), 1)

        def url_generator(page_num):
            query_params = {
                'page': page_num
            }
            if c.search_term:
                query_params['filter'] = c.search_term
            return self.request.current_route_path(_query=query_params)

        c.audit_logs = SqlPage(users_log, page=p, items_per_page=10,
                               url_maker=url_generator)
        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def admin_audit_log_entry(self):
        c = self.load_default_context()
        audit_log_id = self.request.matchdict['audit_log_id']

        c.audit_log_entry = UserLog.query()\
            .options(joinedload(UserLog.user))\
            .options(joinedload(UserLog.repository))\
            .filter(UserLog.user_log_id == audit_log_id).scalar()
        if not c.audit_log_entry:
            raise HTTPNotFound()

        return self._get_template_context(c)
