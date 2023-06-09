# -*- coding: utf-8 -*-

# Copyright (C) 2017-2020 RhodeCode GmbH
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

from rhodecode.lib.jsonalchemy import JsonRaw
from rhodecode.model import meta
from rhodecode.model.db import User, UserLog, Repository


log = logging.getLogger(__name__)

# action as key, and expected action_data as value
ACTIONS_V1 = {
    'user.login.success': {'user_agent': ''},
    'user.login.failure': {'user_agent': ''},
    'user.logout': {'user_agent': ''},
    'user.register': {},
    'user.password.reset_request': {},
    'user.push': {'user_agent': '', 'commit_ids': []},
    'user.pull': {'user_agent': ''},

    'user.create': {'data': {}},
    'user.delete': {'old_data': {}},
    'user.edit': {'old_data': {}},
    'user.edit.permissions': {},
    'user.edit.ip.add': {'ip': {}, 'user': {}},
    'user.edit.ip.delete': {'ip': {}, 'user': {}},
    'user.edit.token.add': {'token': {}, 'user': {}},
    'user.edit.token.delete': {'token': {}, 'user': {}},
    'user.edit.email.add': {'email': ''},
    'user.edit.email.delete': {'email': ''},
    'user.edit.ssh_key.add': {'token': {}, 'user': {}},
    'user.edit.ssh_key.delete': {'token': {}, 'user': {}},
    'user.edit.password_reset.enabled': {},
    'user.edit.password_reset.disabled': {},

    'user_group.create': {'data': {}},
    'user_group.delete': {'old_data': {}},
    'user_group.edit': {'old_data': {}},
    'user_group.edit.permissions': {},
    'user_group.edit.member.add': {'user': {}},
    'user_group.edit.member.delete': {'user': {}},

    'repo.create': {'data': {}},
    'repo.fork': {'data': {}},
    'repo.edit': {'old_data': {}},
    'repo.edit.permissions': {},
    'repo.edit.permissions.branch': {},
    'repo.archive': {'old_data': {}},
    'repo.delete': {'old_data': {}},

    'repo.archive.download': {'user_agent': '', 'archive_name': '',
                              'archive_spec': '', 'archive_cached': ''},

    'repo.permissions.branch_rule.create': {},
    'repo.permissions.branch_rule.edit': {},
    'repo.permissions.branch_rule.delete': {},

    'repo.pull_request.create': '',
    'repo.pull_request.edit': '',
    'repo.pull_request.delete': '',
    'repo.pull_request.close': '',
    'repo.pull_request.merge': '',
    'repo.pull_request.vote': '',
    'repo.pull_request.comment.create': '',
    'repo.pull_request.comment.edit': '',
    'repo.pull_request.comment.delete': '',

    'repo.pull_request.reviewer.add': '',
    'repo.pull_request.reviewer.delete': '',

    'repo.pull_request.observer.add': '',
    'repo.pull_request.observer.delete': '',

    'repo.commit.strip': {'commit_id': ''},
    'repo.commit.comment.create': {'data': {}},
    'repo.commit.comment.delete': {'data': {}},
    'repo.commit.comment.edit': {'data': {}},
    'repo.commit.vote': '',

    'repo.artifact.add': '',
    'repo.artifact.delete': '',

    'repo_group.create': {'data': {}},
    'repo_group.edit': {'old_data': {}},
    'repo_group.edit.permissions': {},
    'repo_group.delete': {'old_data': {}},
}

ACTIONS = ACTIONS_V1

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
    user_log.action_data = action_data or JsonRaw(u'{}')

    user_log.user_ip = ip_address

    user_log.user_id = user_id
    user_log.username = username
    user_log.user_data = user_data or JsonRaw(u'{}')

    user_log.repository_id = repository_id
    user_log.repository_name = repository_name

    user_log.action_date = datetime.datetime.now()

    return user_log


def store_web(*args, **kwargs):
    action_data = {}
    org_action_data = kwargs.pop('action_data', {})
    action_data.update(org_action_data)
    action_data['source'] = SOURCE_WEB
    kwargs['action_data'] = action_data

    return store(*args, **kwargs)


def store_api(*args, **kwargs):
    action_data = {}
    org_action_data = kwargs.pop('action_data', {})
    action_data.update(org_action_data)
    action_data['source'] = SOURCE_API
    kwargs['action_data'] = action_data

    return store(*args, **kwargs)


def store(action, user, action_data=None, user_data=None, ip_addr=None,
          repo=None, sa_session=None, commit=False):
    """
    Audit logger for various actions made by users, typically this
    results in a call such::

        from rhodecode.lib import audit_logger

        audit_logger.store(
            'repo.edit', user=self._rhodecode_user)
        audit_logger.store(
            'repo.delete', action_data={'data': repo_data},
            user=audit_logger.UserWrap(username='itried-login', ip_addr='8.8.8.8'))

        # repo action
        audit_logger.store(
            'repo.delete',
            user=audit_logger.UserWrap(username='itried-login', ip_addr='8.8.8.8'),
            repo=audit_logger.RepoWrap(repo_name='some-repo'))

        # repo action, when we know and have the repository object already
        audit_logger.store(
            'repo.delete', action_data={'source': audit_logger.SOURCE_WEB, },
            user=self._rhodecode_user,
            repo=repo_object)

        # alternative wrapper to the above
        audit_logger.store_web(
            'repo.delete', action_data={},
            user=self._rhodecode_user,
            repo=repo_object)

        # without an user ?
        audit_logger.store(
            'user.login.failure',
            user=audit_logger.UserWrap(
                    username=self.request.params.get('username'),
                    ip_addr=self.request.remote_addr))

    """
    from rhodecode.lib.utils2 import safe_unicode
    from rhodecode.lib.auth import AuthUser

    action_spec = ACTIONS.get(action, None)
    if action_spec is None:
        raise ValueError('Action `{}` is not supported'.format(action))

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

        action_name = safe_unicode(action)
        ip_address = safe_unicode(ip_addr)

        with sa_session.no_autoflush:

            user_log = _store_log(
                action_name=action_name,
                action_data=action_data or {},
                user_id=user_id,
                username=username,
                user_data=user_data or {},
                ip_address=ip_address,
                repository_id=repository_id,
                repository_name=repository_name
            )

            sa_session.add(user_log)
            if commit:
                sa_session.commit()
            entry_id = user_log.entry_id or ''

            update_user_last_activity(sa_session, user_id)

            if commit:
                sa_session.commit()

        log.info('AUDIT[%s]: Logging action: `%s` by user:id:%s[%s] ip:%s',
                 entry_id, action_name, user_id, username, ip_address)

    except Exception:
        log.exception('AUDIT: failed to store audit log')


def update_user_last_activity(sa_session, user_id):
    _last_activity = datetime.datetime.now()
    try:
        sa_session.query(User).filter(User.user_id == user_id).update(
            {"last_activity": _last_activity})
        log.debug(
            'updated user `%s` last activity to:%s', user_id, _last_activity)
    except Exception:
        log.exception("Failed last activity update for user_id: %s", user_id)
        sa_session.rollback()

