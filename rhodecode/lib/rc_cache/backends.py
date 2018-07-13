# -*- coding: utf-8 -*-

# Copyright (C) 2015-2018 RhodeCode GmbH
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
import time
import errno
import logging

import gevent

from dogpile.cache.backends import memory as memory_backend
from dogpile.cache.backends import file as file_backend
from dogpile.cache.backends import redis as redis_backend
from dogpile.cache.backends.file import NO_VALUE, compat, FileLock
from dogpile.cache.util import memoized_property
from lru import LRU as LRUDict


_default_max_size = 1024

log = logging.getLogger(__name__)


class LRUMemoryBackend(memory_backend.MemoryBackend):
    pickle_values = False

    def __init__(self, arguments):
        max_size = arguments.pop('max_size', _default_max_size)
        callback = None
        if arguments.pop('log_max_size_reached', None):
            def evicted(key, value):
                log.debug(
                    'LRU: evicting key `%s` due to max size %s reach', key, max_size)
            callback = evicted

        arguments['cache_dict'] = LRUDict(max_size, callback=callback)
        super(LRUMemoryBackend, self).__init__(arguments)

    def delete(self, key):
        if self._cache.has_key(key):
            del self._cache[key]

    def delete_multi(self, keys):
        for key in keys:
            if self._cache.has_key(key):
                del self._cache[key]


class Serializer(object):
    def _dumps(self, value):
        return compat.pickle.dumps(value)

    def _loads(self, value):
        return compat.pickle.loads(value)


class CustomLockFactory(FileLock):

    @memoized_property
    def _module(self):
        import fcntl
        flock_org = fcntl.flock

        def gevent_flock(fd, operation):
            """
            Gevent compatible flock
            """
            # set non-blocking, this will cause an exception if we cannot acquire a lock
            operation |= fcntl.LOCK_NB
            start_lock_time = time.time()
            timeout = 60 * 5  # 5min
            while True:
                try:
                    flock_org(fd, operation)
                    # lock has been acquired
                    break
                except (OSError, IOError) as e:
                    # raise on other errors than Resource temporarily unavailable
                    if e.errno != errno.EAGAIN:
                        raise
                    elif (time.time() - start_lock_time) > timeout:
                        # waited to much time on a lock, better fail than loop for ever
                        raise

                    log.debug('Failed to acquire lock, retry in 0.1')
                    gevent.sleep(0.1)

        fcntl.flock = gevent_flock
        return fcntl


class FileNamespaceBackend(Serializer, file_backend.DBMBackend):

    def __init__(self, arguments):
        arguments['lock_factory'] = CustomLockFactory
        super(FileNamespaceBackend, self).__init__(arguments)

    def list_keys(self, prefix=''):
        def cond(v):
            if not prefix:
                return True

            if v.startswith(prefix):
                return True
            return False

        with self._dbm_file(True) as dbm:

            return filter(cond, dbm.keys())

    def get_store(self):
        return self.filename

    def get(self, key):
        with self._dbm_file(False) as dbm:
            if hasattr(dbm, 'get'):
                value = dbm.get(key, NO_VALUE)
            else:
                # gdbm objects lack a .get method
                try:
                    value = dbm[key]
                except KeyError:
                    value = NO_VALUE
            if value is not NO_VALUE:
                value = self._loads(value)
            return value

    def set(self, key, value):
        with self._dbm_file(True) as dbm:
            dbm[key] = self._dumps(value)

    def set_multi(self, mapping):
        with self._dbm_file(True) as dbm:
            for key, value in mapping.items():
                dbm[key] = self._dumps(value)


class RedisPickleBackend(Serializer, redis_backend.RedisBackend):
    def list_keys(self, prefix=''):
        if prefix:
            prefix = prefix + '*'
        return self.client.keys(prefix)

    def get_store(self):
        return self.client.connection_pool

    def set(self, key, value):
        if self.redis_expiration_time:
            self.client.setex(key, self.redis_expiration_time,
                              self._dumps(value))
        else:
            self.client.set(key, self._dumps(value))

    def set_multi(self, mapping):
        mapping = dict(
            (k, self._dumps(v))
            for k, v in mapping.items()
        )

        if not self.redis_expiration_time:
            self.client.mset(mapping)
        else:
            pipe = self.client.pipeline()
            for key, value in mapping.items():
                pipe.setex(key, self.redis_expiration_time, value)
            pipe.execute()