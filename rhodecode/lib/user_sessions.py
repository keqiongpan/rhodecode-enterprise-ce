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

import os
import re
import time
import datetime
import dateutil
import pickle

from rhodecode.model.db import DbSession, Session


class CleanupCommand(Exception):
    pass


class BaseAuthSessions(object):
    SESSION_TYPE = None
    NOT_AVAILABLE = 'NOT AVAILABLE'

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
        to_remove = DbSession.query().filter(DbSession.accessed < expiry_date).count()
        DbSession.query().filter(DbSession.accessed < expiry_date).delete()
        Session().commit()
        return to_remove


class FileAuthSessions(BaseAuthSessions):
    SESSION_TYPE = 'file sessions'

    def _get_sessions_dir(self):
        data_dir = self.config.get('beaker.session.data_dir')
        return data_dir

    def _count_on_filesystem(self, path, older_than=0, callback=None):
        value = dict(percent=0, used=0, total=0, items=0, callbacks=0,
                     path=path, text='')
        items_count = 0
        used = 0
        callbacks = 0
        cur_time = time.time()
        for root, dirs, files in os.walk(path):
            for f in files:
                final_path = os.path.join(root, f)
                try:
                    mtime = os.stat(final_path).st_mtime
                    if (cur_time - mtime) > older_than:
                        items_count += 1
                        if callback:
                            callback_res = callback(final_path)
                            callbacks += 1
                        else:
                            used += os.path.getsize(final_path)
                except OSError:
                    pass
        value.update({
            'percent': 100,
            'used': used,
            'total': used,
            'items': items_count,
            'callbacks': callbacks
        })
        return value

    def get_count(self):
        try:
            sessions_dir = self._get_sessions_dir()
            items_count = self._count_on_filesystem(sessions_dir)['items']
        except Exception:
            items_count = self.NOT_AVAILABLE
        return items_count

    def get_expired_count(self, older_than_seconds=0):
        try:
            sessions_dir = self._get_sessions_dir()
            items_count = self._count_on_filesystem(
                sessions_dir, older_than=older_than_seconds)['items']
        except Exception:
            items_count = self.NOT_AVAILABLE
        return items_count

    def clean_sessions(self, older_than_seconds=0):
        # find . -mtime +60 -exec rm {} \;

        sessions_dir = self._get_sessions_dir()

        def remove_item(path):
            os.remove(path)

        stats = self._count_on_filesystem(
            sessions_dir, older_than=older_than_seconds,
            callback=remove_item)
        return stats['callbacks']


class MemcachedAuthSessions(BaseAuthSessions):
    SESSION_TYPE = 'ext:memcached'
    _key_regex = re.compile(r'ITEM (.*_session) \[(.*); (.*)\]')

    def _get_client(self):
        import memcache
        client = memcache.Client([self.config.get('beaker.session.url')])
        return client

    def _get_telnet_client(self, host, port):
        import telnetlib
        client = telnetlib.Telnet(host, port, None)
        return client

    def _run_telnet_cmd(self, client, cmd):
        client.write("%s\n" % cmd)
        return client.read_until('END')

    def key_details(self, client, slab_ids, limit=100):
        """  Return a list of tuples containing keys and details """
        cmd = 'stats cachedump %s %s'
        for slab_id in slab_ids:
            for key in self._key_regex.finditer(
                    self._run_telnet_cmd(client, cmd % (slab_id, limit))):
                yield key

    def get_count(self):
        client = self._get_client()
        count = self.NOT_AVAILABLE
        try:
            slabs = []
            for server, slabs_data in client.get_slabs():
                slabs.extend(slabs_data.keys())

            host, port = client.servers[0].address
            telnet_client = self._get_telnet_client(host, port)
            keys = self.key_details(telnet_client, slabs)
            count = 0
            for _k in keys:
                count += 1
        except Exception:
            return count

        return count

    def get_expired_count(self, older_than_seconds=None):
        return self.NOT_AVAILABLE

    def clean_sessions(self, older_than_seconds=None):
        raise CleanupCommand('Cleanup for this session type not yet available')


class RedisAuthSessions(BaseAuthSessions):
    SESSION_TYPE = 'ext:redis'

    def _get_client(self):
        import redis
        args = {
            'socket_timeout': 60,
            'url': self.config.get('beaker.session.url')
        }

        client = redis.StrictRedis.from_url(**args)
        return client

    def get_count(self):
        client = self._get_client()
        return len(client.keys('beaker_cache:*'))

    def get_expired_count(self, older_than_seconds=None):
        expiry_date = self._seconds_to_date(older_than_seconds)
        return self.NOT_AVAILABLE

    def clean_sessions(self, older_than_seconds=None):
        client = self._get_client()
        expiry_time = time.time() - older_than_seconds
        deleted_keys = 0
        for key in client.keys('beaker_cache:*'):
            data = client.get(key)
            if data:
                json_data = pickle.loads(data)
                try:
                    accessed_time = json_data['_accessed_time']
                except KeyError:
                    accessed_time = 0
                if accessed_time < expiry_time:
                    client.delete(key)
                    deleted_keys += 1

        return deleted_keys


class MemoryAuthSessions(BaseAuthSessions):
    SESSION_TYPE = 'memory'

    def get_count(self):
        return self.NOT_AVAILABLE

    def get_expired_count(self, older_than_seconds=None):
        return self.NOT_AVAILABLE

    def clean_sessions(self, older_than_seconds=None):
        raise CleanupCommand('Cleanup for this session type not yet available')


def get_session_handler(session_type):
    types = {
        'file': FileAuthSessions,
        'ext:memcached': MemcachedAuthSessions,
        'ext:redis': RedisAuthSessions,
        'ext:database': DbAuthSessions,
        'memory': MemoryAuthSessions
    }

    try:
        return types[session_type]
    except KeyError:
        raise ValueError(
            'This type {} is not supported'.format(session_type))
