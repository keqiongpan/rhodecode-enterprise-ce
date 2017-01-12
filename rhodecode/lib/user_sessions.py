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

import datetime
import dateutil
from rhodecode.model.db import DbSession, Session


class CleanupCommand(Exception):
    pass


class BaseAuthSessions(object):
    SESSION_TYPE = None

    def __init__(self, config):
        session_conf = {}
        for k, v in config.items():
            if k.startswith('beaker.session'):
                session_conf[k] = v
        self.config = session_conf

    def get_count(self):
        raise NotImplementedError

    def get_expired_count(self, older_than_seconds=None):
        raise NotImplementedError

    def clean_sessions(self, older_than_seconds=None):
        raise NotImplementedError

    def _seconds_to_date(self, seconds):
        return datetime.datetime.utcnow() - dateutil.relativedelta.relativedelta(
            seconds=seconds)


class DbAuthSessions(BaseAuthSessions):
    SESSION_TYPE = 'ext:database'

    def get_count(self):
        return DbSession.query().count()

    def get_expired_count(self, older_than_seconds=None):
        expiry_date = self._seconds_to_date(older_than_seconds)
        return DbSession.query().filter(DbSession.accessed < expiry_date).count()

    def clean_sessions(self, older_than_seconds=None):
        expiry_date = self._seconds_to_date(older_than_seconds)
        DbSession.query().filter(DbSession.accessed < expiry_date).delete()
        Session().commit()


class FileAuthSessions(BaseAuthSessions):
    SESSION_TYPE = 'file sessions'

    def get_count(self):
        return 'NOT AVAILABLE'

    def get_expired_count(self, older_than_seconds=None):
        return self.get_count()

    def clean_sessions(self, older_than_seconds=None):
        data_dir = self.config.get('beaker.session.data_dir')
        raise CleanupCommand(
            'Please execute this command: '
            '`find . -mtime +60 -exec rm {{}} \;` inside {} directory'.format(
                data_dir))


class MemcachedAuthSessions(BaseAuthSessions):
    SESSION_TYPE = 'ext:memcached'

    def get_count(self):
        return 'NOT AVAILABLE'

    def get_expired_count(self, older_than_seconds=None):
        return self.get_count()

    def clean_sessions(self, older_than_seconds=None):
        raise CleanupCommand('Cleanup for this session type not yet available')


class MemoryAuthSessions(BaseAuthSessions):
    SESSION_TYPE = 'memory'

    def get_count(self):
        return 'NOT AVAILABLE'

    def get_expired_count(self, older_than_seconds=None):
        return self.get_count()

    def clean_sessions(self, older_than_seconds=None):
        raise CleanupCommand('Cleanup for this session type not yet available')


def get_session_handler(session_type):
    types = {
        'file': FileAuthSessions,
        'ext:memcached': MemcachedAuthSessions,
        'ext:database': DbAuthSessions,
        'memory': MemoryAuthSessions
    }

    try:
        return types[session_type]
    except KeyError:
        raise ValueError(
            'This type {} is not supported'.format(session_type))
