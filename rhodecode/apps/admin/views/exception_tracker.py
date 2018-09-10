# -*- coding: utf-8 -*-

# Copyright (C) 2018-2018 RhodeCode GmbH
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
import os
import logging

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from rhodecode.apps._base import BaseAppView
from rhodecode.apps.admin.navigation import navigation_list
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAllDecorator, CSRFRequired)
from rhodecode.lib.utils2 import time_to_utcdatetime, safe_int
from rhodecode.lib import exc_tracking

log = logging.getLogger(__name__)


class ExceptionsTrackerView(BaseAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.navlist = navigation_list(self.request)
        return c

    def count_all_exceptions(self):
        exc_store_path = exc_tracking.get_exc_store()
        count = 0
        for fname in os.listdir(exc_store_path):
            parts = fname.split('_', 2)
            if not len(parts) == 3:
                continue
            count +=1
        return count

    def get_all_exceptions(self, read_metadata=False, limit=None):
        exc_store_path = exc_tracking.get_exc_store()
        exception_list = []

        def key_sorter(val):
            try:
                return val.split('_')[-1]
            except Exception:
                return 0
        count = 0
        for fname in reversed(sorted(os.listdir(exc_store_path), key=key_sorter)):

            parts = fname.split('_', 2)
            if not len(parts) == 3:
                continue

            exc_id, app_type, exc_timestamp = parts

            exc = {'exc_id': exc_id, 'app_type': app_type, 'exc_type': 'unknown',
                   'exc_utc_date': '', 'exc_timestamp': exc_timestamp}

            if read_metadata:
                full_path = os.path.join(exc_store_path, fname)
                if not os.path.isfile(full_path):
                    continue
                try:
                    # we can read our metadata
                    with open(full_path, 'rb') as f:
                        exc_metadata = exc_tracking.exc_unserialize(f.read())
                        exc.update(exc_metadata)
                except Exception:
                    log.exception('Failed to read exc data from:{}'.format(full_path))
                    pass

            # convert our timestamp to a date obj, for nicer representation
            exc['exc_utc_date'] = time_to_utcdatetime(exc['exc_timestamp'])
            exception_list.append(exc)

            count += 1
            if limit and count >= limit:
                break
        return exception_list

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_exception_tracker', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def browse_exceptions(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'exceptions_browse'
        c.limit = safe_int(self.request.GET.get('limit')) or 50
        c.next_limit = c.limit + 50
        c.exception_list = self.get_all_exceptions(read_metadata=True, limit=c.limit)
        c.exception_list_count = self.count_all_exceptions()
        c.exception_store_dir = exc_tracking.get_exc_store()
        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @view_config(
        route_name='admin_settings_exception_tracker_show', request_method='GET',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def exception_show(self):
        _ = self.request.translate
        c = self.load_default_context()

        c.active = 'exceptions'
        c.exception_id = self.request.matchdict['exception_id']
        c.traceback = exc_tracking.read_exception(c.exception_id, prefix=None)
        return self._get_template_context(c)

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_exception_tracker_delete_all', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def exception_delete_all(self):
        _ = self.request.translate
        c = self.load_default_context()

        c.active = 'exceptions'
        all_exc = self.get_all_exceptions()
        exc_count = len(all_exc)
        for exc in all_exc:
            exc_tracking.delete_exception(exc['exc_id'], prefix=None)

        h.flash(_('Removed {} Exceptions').format(exc_count), category='success')
        raise HTTPFound(h.route_path('admin_settings_exception_tracker'))

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    @CSRFRequired()
    @view_config(
        route_name='admin_settings_exception_tracker_delete', request_method='POST',
        renderer='rhodecode:templates/admin/settings/settings.mako')
    def exception_delete(self):
        _ = self.request.translate
        c = self.load_default_context()

        c.active = 'exceptions'
        c.exception_id = self.request.matchdict['exception_id']
        exc_tracking.delete_exception(c.exception_id, prefix=None)

        h.flash(_('Removed Exception {}').format(c.exception_id), category='success')
        raise HTTPFound(h.route_path('admin_settings_exception_tracker'))
