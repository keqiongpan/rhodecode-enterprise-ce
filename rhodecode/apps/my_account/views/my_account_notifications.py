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

import logging

from pyramid.httpexceptions import (
    HTTPFound, HTTPNotFound, HTTPInternalServerError)
from pyramid.view import view_config

from rhodecode.apps._base import BaseAppView
from rhodecode.lib.auth import LoginRequired, NotAnonymous, CSRFRequired

from rhodecode.lib import helpers as h
from rhodecode.lib.helpers import SqlPage
from rhodecode.lib.utils2 import safe_int
from rhodecode.model.db import Notification
from rhodecode.model.notification import NotificationModel
from rhodecode.model.meta import Session


log = logging.getLogger(__name__)


class MyAccountNotificationsView(BaseAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.user = c.auth_user.get_instance()

        return c

    def _has_permissions(self, notification):
        def is_owner():
            user_id = self._rhodecode_db_user.user_id
            for user_notification in notification.notifications_to_users:
                if user_notification.user.user_id == user_id:
                    return True
            return False
        return h.HasPermissionAny('hg.admin')() or is_owner()

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='notifications_show_all', request_method='GET',
        renderer='rhodecode:templates/admin/notifications/notifications_show_all.mako')
    def notifications_show_all(self):
        c = self.load_default_context()

        c.unread_count = NotificationModel().get_unread_cnt_for_user(
            self._rhodecode_db_user.user_id)

        _current_filter = self.request.GET.getall('type') or ['unread']

        notifications = NotificationModel().get_for_user(
            self._rhodecode_db_user.user_id,
            filter_=_current_filter)

        p = safe_int(self.request.GET.get('page', 1), 1)

        def url_generator(page_num):
            query_params = {
                'page': page_num
            }
            _query = self.request.GET.mixed()
            query_params.update(_query)
            return self.request.current_route_path(_query=query_params)

        c.notifications = SqlPage(notifications, page=p, items_per_page=10,
                                  url_maker=url_generator)

        c.unread_type = 'unread'
        c.all_type = 'all'
        c.pull_request_type = Notification.TYPE_PULL_REQUEST
        c.comment_type = [Notification.TYPE_CHANGESET_COMMENT,
                          Notification.TYPE_PULL_REQUEST_COMMENT]

        c.current_filter = 'unread'  # default filter

        if _current_filter == [c.pull_request_type]:
            c.current_filter = 'pull_request'
        elif _current_filter == c.comment_type:
            c.current_filter = 'comment'
        elif _current_filter == [c.unread_type]:
            c.current_filter = 'unread'
        elif _current_filter == [c.all_type]:
            c.current_filter = 'all'
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='notifications_mark_all_read', request_method='POST',
        renderer='rhodecode:templates/admin/notifications/notifications_show_all.mako')
    def notifications_mark_all_read(self):
        NotificationModel().mark_all_read_for_user(
            self._rhodecode_db_user.user_id,
            filter_=self.request.GET.getall('type'))
        Session().commit()
        raise HTTPFound(h.route_path('notifications_show_all'))

    @LoginRequired()
    @NotAnonymous()
    @view_config(
        route_name='notifications_show', request_method='GET',
        renderer='rhodecode:templates/admin/notifications/notifications_show.mako')
    def notifications_show(self):
        c = self.load_default_context()
        notification_id = self.request.matchdict['notification_id']
        notification = Notification.get_or_404(notification_id)

        if not self._has_permissions(notification):
            log.debug('User %s does not have permission to access notification',
                      self._rhodecode_user)
            raise HTTPNotFound()

        u_notification = NotificationModel().get_user_notification(
            self._rhodecode_db_user.user_id, notification)
        if not u_notification:
            log.debug('User %s notification does not exist',
                      self._rhodecode_user)
            raise HTTPNotFound()

        # when opening this notification, mark it as read for this use
        if not u_notification.read:
            u_notification.mark_as_read()
            Session().commit()

        c.notification = notification

        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='notifications_update', request_method='POST',
        renderer='json_ext')
    def notification_update(self):
        notification_id = self.request.matchdict['notification_id']
        notification = Notification.get_or_404(notification_id)

        if not self._has_permissions(notification):
            log.debug('User %s does not have permission to access notification',
                      self._rhodecode_user)
            raise HTTPNotFound()

        try:
            # updates notification read flag
            NotificationModel().mark_read(
                self._rhodecode_user.user_id, notification)
            Session().commit()
            return 'ok'
        except Exception:
            Session().rollback()
            log.exception("Exception updating a notification item")

        raise HTTPInternalServerError()

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    @view_config(
        route_name='notifications_delete', request_method='POST',
        renderer='json_ext')
    def notification_delete(self):
        notification_id = self.request.matchdict['notification_id']
        notification = Notification.get_or_404(notification_id)
        if not self._has_permissions(notification):
            log.debug('User %s does not have permission to access notification',
                      self._rhodecode_user)
            raise HTTPNotFound()

        try:
            # deletes only notification2user
            NotificationModel().delete(
                self._rhodecode_user.user_id, notification)
            Session().commit()
            return 'ok'
        except Exception:
            Session().rollback()
            log.exception("Exception deleting a notification item")

        raise HTTPInternalServerError()
