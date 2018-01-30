# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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

from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.tests import (
    TestController, TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS,
    TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS)
from rhodecode.tests.fixture import Fixture

from rhodecode.model.db import Notification, User
from rhodecode.model.user import UserModel
from rhodecode.model.notification import NotificationModel
from rhodecode.model.meta import Session

fixture = Fixture()


def route_path(name, params=None, **kwargs):
    import urllib
    from rhodecode.apps._base import ADMIN_PREFIX

    base_url = {
        'notifications_show_all': ADMIN_PREFIX + '/notifications',
        'notifications_mark_all_read': ADMIN_PREFIX + '/notifications/mark_all_read',
        'notifications_show': ADMIN_PREFIX + '/notifications/{notification_id}',
        'notifications_update': ADMIN_PREFIX + '/notifications/{notification_id}/update',
        'notifications_delete': ADMIN_PREFIX + '/notifications/{notification_id}/delete',

    }[name].format(**kwargs)

    if params:
        base_url = '{}?{}'.format(base_url, urllib.urlencode(params))
    return base_url


class TestNotificationsController(TestController):

    def teardown_method(self, method):
        for n in Notification.query().all():
            inst = Notification.get(n.notification_id)
            Session().delete(inst)
        Session().commit()

    def test_show_all(self, user_util):
        user = user_util.create_user(password='qweqwe')
        user_id = user.user_id
        self.log_user(user.username, 'qweqwe')

        response = self.app.get(
            route_path('notifications_show_all', params={'type': 'all'}))
        response.mustcontain(
            '<div class="table">No notifications here yet</div>')

        notification = NotificationModel().create(
            created_by=user_id, notification_subject=u'test_notification_1',
            notification_body=u'notification_1', recipients=[user_id])
        Session().commit()
        notification_id = notification.notification_id

        response = self.app.get(route_path('notifications_show_all',
                                           params={'type': 'all'}))
        response.mustcontain('id="notification_%s"' % notification_id)

    def test_show_unread(self, user_util):
        user = user_util.create_user(password='qweqwe')
        user_id = user.user_id
        self.log_user(user.username, 'qweqwe')

        response = self.app.get(route_path('notifications_show_all'))
        response.mustcontain(
            '<div class="table">No notifications here yet</div>')

        notification = NotificationModel().create(
            created_by=user_id, notification_subject=u'test_notification_1',
            notification_body=u'notification_1', recipients=[user_id])

        # mark the USER notification as unread
        user_notification = NotificationModel().get_user_notification(
            user_id, notification)
        user_notification.read = False

        Session().commit()
        notification_id = notification.notification_id

        response = self.app.get(route_path('notifications_show_all'))
        response.mustcontain('id="notification_%s"' % notification_id)
        response.mustcontain('<div class="desc unread')

    @pytest.mark.parametrize('user,password', [
        (TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS),
        (TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS),
    ])
    def test_delete(self, user, password, user_util):
        self.log_user(user, password)
        cur_user = self._get_logged_user()

        u1 = user_util.create_user()
        u2 = user_util.create_user()

        # make notifications
        notification = NotificationModel().create(
            created_by=cur_user, notification_subject=u'test',
            notification_body=u'hi there', recipients=[cur_user, u1, u2])
        Session().commit()
        u1 = User.get(u1.user_id)
        u2 = User.get(u2.user_id)

        # check DB
        get_notif = lambda un: [x.notification for x in un]
        assert get_notif(cur_user.notifications) == [notification]
        assert get_notif(u1.notifications) == [notification]
        assert get_notif(u2.notifications) == [notification]
        cur_usr_id = cur_user.user_id

        response = self.app.post(
            route_path('notifications_delete',
                       notification_id=notification.notification_id),
            params={'csrf_token': self.csrf_token})
        assert response.json == 'ok'

        cur_user = User.get(cur_usr_id)
        assert cur_user.notifications == []

    @pytest.mark.parametrize('user,password', [
        (TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS),
        (TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS),
    ])
    def test_show(self, user, password, user_util):
        self.log_user(user, password)
        cur_user = self._get_logged_user()
        u1 = user_util.create_user()
        u2 = user_util.create_user()

        subject = u'test'
        notif_body = u'hi there'
        notification = NotificationModel().create(
            created_by=cur_user, notification_subject=subject,
            notification_body=notif_body, recipients=[cur_user, u1, u2])

        response = self.app.get(
            route_path('notifications_show',
                       notification_id=notification.notification_id))

        response.mustcontain(subject)
        response.mustcontain(notif_body)

    @pytest.mark.parametrize('user,password', [
        (TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS),
        (TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS),
    ])
    def test_update(self, user, password, user_util):
        self.log_user(user, password)
        cur_user = self._get_logged_user()
        u1 = user_util.create_user()
        u2 = user_util.create_user()

        # make notifications
        recipients = [cur_user, u1, u2]
        notification = NotificationModel().create(
            created_by=cur_user, notification_subject=u'test',
            notification_body=u'hi there', recipients=recipients)
        Session().commit()

        for u_obj in recipients:
            # if it's current user, he has his message already read
            read = u_obj.username == user
            assert len(u_obj.notifications) == 1
            assert u_obj.notifications[0].read == read

        response = self.app.post(
            route_path('notifications_update',
                       notification_id=notification.notification_id),
            params={'csrf_token': self.csrf_token})
        assert response.json == 'ok'

        cur_user = self._get_logged_user()
        assert True is cur_user.notifications[0].read
