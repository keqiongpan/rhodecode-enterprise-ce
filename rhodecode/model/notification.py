# -*- coding: utf-8 -*-

# Copyright (C) 2011-2020 RhodeCode GmbH
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
Model for notifications
"""

import logging
import traceback

import premailer
from pyramid.threadlocal import get_current_request
from sqlalchemy.sql.expression import false, true

import rhodecode
from rhodecode.lib import helpers as h
from rhodecode.model import BaseModel
from rhodecode.model.db import Notification, User, UserNotification
from rhodecode.model.meta import Session
from rhodecode.translation import TranslationString

log = logging.getLogger(__name__)


class NotificationModel(BaseModel):

    cls = Notification

    def __get_notification(self, notification):
        if isinstance(notification, Notification):
            return notification
        elif isinstance(notification, (int, long)):
            return Notification.get(notification)
        else:
            if notification:
                raise Exception('notification must be int, long or Instance'
                                ' of Notification got %s' % type(notification))

    def create(
            self, created_by, notification_subject='', notification_body='',
            notification_type=Notification.TYPE_MESSAGE, recipients=None,
            mention_recipients=None, with_email=True, email_kwargs=None):
        """

        Creates notification of given type

        :param created_by: int, str or User instance. User who created this
            notification
        :param notification_subject: subject of notification itself,
            it will be generated automatically from notification_type if not specified
        :param notification_body: body of notification text
            it will be generated automatically from notification_type if not specified
        :param notification_type: type of notification, based on that we
            pick templates
        :param recipients: list of int, str or User objects, when None
            is given send to all admins
        :param mention_recipients: list of int, str or User objects,
            that were mentioned
        :param with_email: send email with this notification
        :param email_kwargs: dict with arguments to generate email
        """

        from rhodecode.lib.celerylib import tasks, run_task

        if recipients and not getattr(recipients, '__iter__', False):
            raise Exception('recipients must be an iterable object')

        if not (notification_subject and notification_body) and not notification_type:
            raise ValueError('notification_subject, and notification_body '
                             'cannot be empty when notification_type is not specified')

        created_by_obj = self._get_user(created_by)

        if not created_by_obj:
            raise Exception('unknown user %s' % created_by)

        # default MAIN body if not given
        email_kwargs = email_kwargs or {'body': notification_body}
        mention_recipients = mention_recipients or set()

        if recipients is None:
            # recipients is None means to all admins
            recipients_objs = User.query().filter(User.admin == true()).all()
            log.debug('sending notifications %s to admins: %s',
                      notification_type, recipients_objs)
        else:
            recipients_objs = set()
            for u in recipients:
                obj = self._get_user(u)
                if obj:
                    recipients_objs.add(obj)
                else:  # we didn't find this user, log the error and carry on
                    log.error('cannot notify unknown user %r', u)

            if not recipients_objs:
                raise Exception('no valid recipients specified')

            log.debug('sending notifications %s to %s',
                      notification_type, recipients_objs)

        # add mentioned users into recipients
        final_recipients = set(recipients_objs).union(mention_recipients)

        (subject, email_body, email_body_plaintext) = \
            EmailNotificationModel().render_email(notification_type, **email_kwargs)

        if not notification_subject:
            notification_subject = subject

        if not notification_body:
            notification_body = email_body_plaintext

        notification = Notification.create(
            created_by=created_by_obj, subject=notification_subject,
            body=notification_body, recipients=final_recipients,
            type_=notification_type
        )

        if not with_email:  # skip sending email, and just create notification
            return notification

        # don't send email to person who created this comment
        rec_objs = set(recipients_objs).difference({created_by_obj})

        # now notify all recipients in question

        for recipient in rec_objs.union(mention_recipients):
            # inject current recipient
            email_kwargs['recipient'] = recipient
            email_kwargs['mention'] = recipient in mention_recipients
            (subject, email_body, email_body_plaintext) = EmailNotificationModel().render_email(
                notification_type, **email_kwargs)

            extra_headers = None
            if 'thread_ids' in email_kwargs:
                extra_headers = {'thread_ids': email_kwargs.pop('thread_ids')}

            log.debug('Creating notification email task for user:`%s`', recipient)
            task = run_task(
                tasks.send_email, recipient.email, subject,
                email_body_plaintext, email_body, extra_headers=extra_headers)
            log.debug('Created email task: %s', task)

        return notification

    def delete(self, user, notification):
        # we don't want to remove actual notification just the assignment
        try:
            notification = self.__get_notification(notification)
            user = self._get_user(user)
            if notification and user:
                obj = UserNotification.query()\
                    .filter(UserNotification.user == user)\
                    .filter(UserNotification.notification == notification)\
                    .one()
                Session().delete(obj)
                return True
        except Exception:
            log.error(traceback.format_exc())
            raise

    def get_for_user(self, user, filter_=None):
        """
        Get mentions for given user, filter them if filter dict is given
        """
        user = self._get_user(user)

        q = UserNotification.query()\
            .filter(UserNotification.user == user)\
            .join((
                Notification, UserNotification.notification_id ==
                Notification.notification_id))
        if filter_ == ['all']:
            q = q  # no filter
        elif filter_ == ['unread']:
            q = q.filter(UserNotification.read == false())
        elif filter_:
            q = q.filter(Notification.type_.in_(filter_))

        return q

    def mark_read(self, user, notification):
        try:
            notification = self.__get_notification(notification)
            user = self._get_user(user)
            if notification and user:
                obj = UserNotification.query()\
                    .filter(UserNotification.user == user)\
                    .filter(UserNotification.notification == notification)\
                    .one()
                obj.read = True
                Session().add(obj)
                return True
        except Exception:
            log.error(traceback.format_exc())
            raise

    def mark_all_read_for_user(self, user, filter_=None):
        user = self._get_user(user)
        q = UserNotification.query()\
            .filter(UserNotification.user == user)\
            .filter(UserNotification.read == false())\
            .join((
                Notification, UserNotification.notification_id ==
                Notification.notification_id))
        if filter_ == ['unread']:
            q = q.filter(UserNotification.read == false())
        elif filter_:
            q = q.filter(Notification.type_.in_(filter_))

        # this is a little inefficient but sqlalchemy doesn't support
        # update on joined tables :(
        for obj in q.all():
            obj.read = True
            Session().add(obj)

    def get_unread_cnt_for_user(self, user):
        user = self._get_user(user)
        return UserNotification.query()\
            .filter(UserNotification.read == false())\
            .filter(UserNotification.user == user).count()

    def get_unread_for_user(self, user):
        user = self._get_user(user)
        return [x.notification for x in UserNotification.query()
                .filter(UserNotification.read == false())
                .filter(UserNotification.user == user).all()]

    def get_user_notification(self, user, notification):
        user = self._get_user(user)
        notification = self.__get_notification(notification)

        return UserNotification.query()\
            .filter(UserNotification.notification == notification)\
            .filter(UserNotification.user == user).scalar()

    def make_description(self, notification, translate, show_age=True):
        """
        Creates a human readable description based on properties
        of notification object
        """
        _ = translate
        _map = {
            notification.TYPE_CHANGESET_COMMENT: [
                _('%(user)s commented on commit %(date_or_age)s'),
                _('%(user)s commented on commit at %(date_or_age)s'),
                ],
            notification.TYPE_MESSAGE: [
                _('%(user)s sent message %(date_or_age)s'),
                _('%(user)s sent message at %(date_or_age)s'),
                ],
            notification.TYPE_MENTION: [
                _('%(user)s mentioned you %(date_or_age)s'),
                _('%(user)s mentioned you at %(date_or_age)s'),
                ],
            notification.TYPE_REGISTRATION: [
                _('%(user)s registered in RhodeCode %(date_or_age)s'),
                _('%(user)s registered in RhodeCode at %(date_or_age)s'),
                ],
            notification.TYPE_PULL_REQUEST: [
                _('%(user)s opened new pull request %(date_or_age)s'),
                _('%(user)s opened new pull request at %(date_or_age)s'),
                ],
            notification.TYPE_PULL_REQUEST_UPDATE: [
                _('%(user)s updated pull request %(date_or_age)s'),
                _('%(user)s updated pull request at %(date_or_age)s'),
            ],
            notification.TYPE_PULL_REQUEST_COMMENT: [
                _('%(user)s commented on pull request %(date_or_age)s'),
                _('%(user)s commented on pull request at %(date_or_age)s'),
                ],
        }

        templates = _map[notification.type_]

        if show_age:
            template = templates[0]
            date_or_age = h.age(notification.created_on)
            if translate:
                date_or_age = translate(date_or_age)

            if isinstance(date_or_age, TranslationString):
                date_or_age = date_or_age.interpolate()

        else:
            template = templates[1]
            date_or_age = h.format_date(notification.created_on)

        return template % {
            'user': notification.created_by_user.username,
            'date_or_age': date_or_age,
        }


# Templates for Titles, that could be overwritten by rcextensions
# Title of email for pull-request update
EMAIL_PR_UPDATE_SUBJECT_TEMPLATE = ''
# Title of email for request for pull request review
EMAIL_PR_REVIEW_SUBJECT_TEMPLATE = ''

# Title of email for general comment on pull request
EMAIL_PR_COMMENT_SUBJECT_TEMPLATE = ''
# Title of email for general comment which includes status change on pull request
EMAIL_PR_COMMENT_STATUS_CHANGE_SUBJECT_TEMPLATE = ''
# Title of email for inline comment on a file in pull request
EMAIL_PR_COMMENT_FILE_SUBJECT_TEMPLATE = ''

# Title of email for general comment on commit
EMAIL_COMMENT_SUBJECT_TEMPLATE = ''
# Title of email for general comment which includes status change on commit
EMAIL_COMMENT_STATUS_CHANGE_SUBJECT_TEMPLATE = ''
# Title of email for inline comment on a file in commit
EMAIL_COMMENT_FILE_SUBJECT_TEMPLATE = ''


class EmailNotificationModel(BaseModel):
    TYPE_COMMIT_COMMENT = Notification.TYPE_CHANGESET_COMMENT
    TYPE_REGISTRATION = Notification.TYPE_REGISTRATION
    TYPE_PULL_REQUEST = Notification.TYPE_PULL_REQUEST
    TYPE_PULL_REQUEST_COMMENT = Notification.TYPE_PULL_REQUEST_COMMENT
    TYPE_PULL_REQUEST_UPDATE = Notification.TYPE_PULL_REQUEST_UPDATE
    TYPE_MAIN = Notification.TYPE_MESSAGE

    TYPE_PASSWORD_RESET = 'password_reset'
    TYPE_PASSWORD_RESET_CONFIRMATION = 'password_reset_confirmation'
    TYPE_EMAIL_TEST = 'email_test'
    TYPE_EMAIL_EXCEPTION = 'exception'
    TYPE_UPDATE_AVAILABLE = 'update_available'
    TYPE_TEST = 'test'

    email_types = {
        TYPE_MAIN:
            'rhodecode:templates/email_templates/main.mako',
        TYPE_TEST:
            'rhodecode:templates/email_templates/test.mako',
        TYPE_EMAIL_EXCEPTION:
            'rhodecode:templates/email_templates/exception_tracker.mako',
        TYPE_UPDATE_AVAILABLE:
            'rhodecode:templates/email_templates/update_available.mako',
        TYPE_EMAIL_TEST:
            'rhodecode:templates/email_templates/email_test.mako',
        TYPE_REGISTRATION:
            'rhodecode:templates/email_templates/user_registration.mako',
        TYPE_PASSWORD_RESET:
            'rhodecode:templates/email_templates/password_reset.mako',
        TYPE_PASSWORD_RESET_CONFIRMATION:
            'rhodecode:templates/email_templates/password_reset_confirmation.mako',
        TYPE_COMMIT_COMMENT:
            'rhodecode:templates/email_templates/commit_comment.mako',
        TYPE_PULL_REQUEST:
            'rhodecode:templates/email_templates/pull_request_review.mako',
        TYPE_PULL_REQUEST_COMMENT:
            'rhodecode:templates/email_templates/pull_request_comment.mako',
        TYPE_PULL_REQUEST_UPDATE:
            'rhodecode:templates/email_templates/pull_request_update.mako',
    }

    premailer_instance = premailer.Premailer(
        cssutils_logging_level=logging.ERROR,
        cssutils_logging_handler=logging.getLogger().handlers[0]
        if logging.getLogger().handlers else None,
    )

    def __init__(self):
        """
        Example usage::

            (subject, email_body, email_body_plaintext) = EmailNotificationModel().render_email(
                EmailNotificationModel.TYPE_TEST, **email_kwargs)

        """
        super(EmailNotificationModel, self).__init__()
        self.rhodecode_instance_name = rhodecode.CONFIG.get('rhodecode_title')

    def _update_kwargs_for_render(self, kwargs):
        """
        Inject params required for Mako rendering

        :param kwargs:
        """

        kwargs['rhodecode_instance_name'] = self.rhodecode_instance_name
        kwargs['rhodecode_version'] = rhodecode.__version__
        instance_url = h.route_url('home')
        _kwargs = {
            'instance_url': instance_url,
            'whitespace_filter': self.whitespace_filter,
            'email_pr_update_subject_template': EMAIL_PR_UPDATE_SUBJECT_TEMPLATE,
            'email_pr_review_subject_template': EMAIL_PR_REVIEW_SUBJECT_TEMPLATE,
            'email_pr_comment_subject_template': EMAIL_PR_COMMENT_SUBJECT_TEMPLATE,
            'email_pr_comment_status_change_subject_template': EMAIL_PR_COMMENT_STATUS_CHANGE_SUBJECT_TEMPLATE,
            'email_pr_comment_file_subject_template': EMAIL_PR_COMMENT_FILE_SUBJECT_TEMPLATE,
            'email_comment_subject_template': EMAIL_COMMENT_SUBJECT_TEMPLATE,
            'email_comment_status_change_subject_template': EMAIL_COMMENT_STATUS_CHANGE_SUBJECT_TEMPLATE,
            'email_comment_file_subject_template': EMAIL_COMMENT_FILE_SUBJECT_TEMPLATE,
        }
        _kwargs.update(kwargs)
        return _kwargs

    def whitespace_filter(self, text):
        return text.replace('\n', '').replace('\t', '')

    def get_renderer(self, type_, request):
        template_name = self.email_types[type_]
        return request.get_partial_renderer(template_name)

    def render_email(self, type_, **kwargs):
        """
        renders template for email, and returns a tuple of
        (subject, email_headers, email_html_body, email_plaintext_body)
        """
        # translator and helpers inject
        _kwargs = self._update_kwargs_for_render(kwargs)
        request = get_current_request()
        email_template = self.get_renderer(type_, request=request)

        subject = email_template.render('subject', **_kwargs)

        try:
            body_plaintext = email_template.render('body_plaintext', **_kwargs)
        except AttributeError:
            # it's not defined in template, ok we can skip it
            body_plaintext = ''

        # render WHOLE template
        body = email_template.render(None, **_kwargs)

        try:
            # Inline CSS styles and conversion
            body = self.premailer_instance.transform(body)
        except Exception:
            log.exception('Failed to parse body with premailer')
            pass

        return subject, body, body_plaintext
