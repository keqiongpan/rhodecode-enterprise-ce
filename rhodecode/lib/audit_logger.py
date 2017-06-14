# -*- coding: utf-8 -*-

# Copyright (C) 2017-2017 RhodeCode GmbH
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
import datetime

from rhodecode.model import meta
from rhodecode.model.db import User, UserLog, Repository


log = logging.getLogger(__name__)


ACTIONS = {
    'user.login.success': {},
    'user.login.failure': {},
    'user.logout': {},
    'user.password.reset_request': {},
    'user.push': {},
    'user.pull': {},

    'repo.create': {},
    'repo.edit': {},
    'repo.edit.permissions': {},
    'repo.delete': {},
    'repo.commit.strip': {},
    'repo.archive.download': {},
}

SOURCE_WEB = 'source_web'
SOURCE_API = 'source_api'


class UserWrap(object):
    """
    Fake object used to imitate AuthUser
    """

    def __init__(self, user_id=None, username=None, ip_addr=None):
        self.user_id = user_id
        self.username = username
        self.ip_addr = ip_addr


class RepoWrap(object):
    """
    Fake object used to imitate RepoObject that audit logger requires
    """

    def __init__(self, repo_id=None, repo_name=None):
        self.repo_id = repo_id
        self.repo_name = repo_name


def _store_log(action_name, action_data, user_id, username, user_data,
               ip_address, repository_id, repository_name):
    user_log = UserLog()
    user_log.version = UserLog.VERSION_2

    user_log.action = action_name
    user_log.action_data = action_data

    user_log.user_ip = ip_address

    user_log.user_id = user_id
    user_log.username = username
    user_log.user_data = user_data

    user_log.repository_id = repository_id
    user_log.repository_name = repository_name

    user_log.action_date = datetime.datetime.now()

    log.info('AUDIT: Logging action: `%s` by user:id:%s[%s] ip:%s',
             action_name, user_id, username, ip_address)

    return user_log


def store(
        action, user, action_data=None, user_data=None, ip_addr=None,
        repo=None, sa_session=None, commit=False):
    """
    Audit logger for various actions made by users, typically this results in a call such::

        from rhodecode.lib import audit_logger

        audit_logger.store(
            action='repo.edit', user=self._rhodecode_user)
        audit_logger.store(
            action='repo.delete', action_data={'repo_data': repo_data},
            user=audit_logger.UserWrap(username='itried-login', ip_addr='8.8.8.8'))

        # repo action
        audit_logger.store(
            action='repo.delete',
            user=audit_logger.UserWrap(username='itried-login', ip_addr='8.8.8.8'),
            repo=audit_logger.RepoWrap(repo_name='some-repo'))

        # repo action, when we know and have the repository object already
        audit_logger.store(
            action='repo.delete',
            action_data={'source': audit_logger.SOURCE_WEB, },
            user=self._rhodecode_user,
            repo=repo_object)

        # without an user ?
        audit_logger.store(
            action='user.login.failure',
            user=audit_logger.UserWrap(
                    username=self.request.params.get('username'),
                    ip_addr=self.request.remote_addr))

    """
    from rhodecode.lib.utils2 import safe_unicode
    from rhodecode.lib.auth import AuthUser

    if action not in ACTIONS:
        raise ValueError('Action `{}` not in valid actions'.format(action))

    if not sa_session:
        sa_session = meta.Session()

    try:
        username = getattr(user, 'username', None)
        if not username:
            pass

        user_id = getattr(user, 'user_id', None)
        if not user_id:
            # maybe we have username ? Try to figure user_id from username
            if username:
                user_id = getattr(
                    User.get_by_username(username), 'user_id', None)

        ip_addr = ip_addr or getattr(user, 'ip_addr', None)
        if not ip_addr:
            pass

        if not user_data:
            # try to get this from the auth user
            if isinstance(user, AuthUser):
                user_data = {
                    'username': user.username,
                    'email': user.email,
                }

        repository_name = getattr(repo, 'repo_name', None)
        repository_id = getattr(repo, 'repo_id', None)
        if not repository_id:
            # maybe we have repo_name ? Try to figure repo_id from repo_name
            if repository_name:
                repository_id = getattr(
                    Repository.get_by_repo_name(repository_name), 'repo_id', None)

        user_log = _store_log(
            action_name=safe_unicode(action),
            action_data=action_data or {},
            user_id=user_id,
            username=username,
            user_data=user_data or {},
            ip_address=safe_unicode(ip_addr),
            repository_id=repository_id,
            repository_name=repository_name
        )
        sa_session.add(user_log)
        if commit:
            sa_session.commit()

    except Exception:
        log.exception('AUDIT: failed to store audit log')
