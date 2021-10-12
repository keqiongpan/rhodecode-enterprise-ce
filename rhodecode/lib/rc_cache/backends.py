# -*- coding: utf-8 -*-

# Copyright (C) 2015-2020 RhodeCode GmbH
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

import msgpack
import gevent
import redis

from dogpile.cache.api import CachedValue
from dogpile.cache.backends import memory as memory_backend
from dogpile.cache.backends import file as file_backend
from dogpile.cache.backends import redis as redis_backend
from dogpile.cache.backends.file import NO_VALUE, compat, FileLock
from dogpile.cache.util import memoized_property

from pyramid.settings import asbool

from rhodecode.lib.memory_lru_dict import LRUDict, LRUDictDebug


_default_max_size = 1024

log = logging.getLogger(__name__)


class LRUMemoryBackend(memory_backend.MemoryBackend):
    key_prefix = 'lru_mem_backend'
    pickle_values = False

    def __init__(self, arguments):
        max_size = arguments.pop('max_size', _default_max_size)

        LRUDictClass = LRUDict
        if arguments.pop('log_key_count', None):
            LRUDictClass = LRUDictDebug

        arguments['cache_dict'] = LRUDictClass(max_size)
        super(LRUMemoryBackend, self).__init__(arguments)

    def delete(self, key):
        try:
            del self._cache[key]
        except KeyError:
            # we don't care if key isn't there at deletion
            pass

    def delete_multi(self, keys):
        for key in keys:
            self.delete(key)


class PickleSerializer(object):

    def _dumps(self, value, safe=False):
        try:
            return compat.pickle.dumps(value)
        except Exception:
            if safe:
                return NO_VALUE
            else:
                raise

    def _loads(self, value, safe=True):
        try:
            return compat.pickle.loads(value)
        except Exception:
            if safe:
                return NO_VALUE
            else:
                raise


class MsgPackSerializer(object):

    def _dumps(self, value, safe=False):
        try:
            return msgpack.packb(value)
        except Exception:
            if safe:
                return NO_VALUE
            else:
                raise

    def _loads(self, value, safe=True):
        """
        pickle maintained the `CachedValue` wrapper of the tuple
        msgpack does not, so it must be added back in.
       """
        try:
            value = msgpack.unpackb(value, use_list=False)
            return CachedValue(*value)
        except Exception:
            if safe:
                return NO_VALUE
            else:
                raise


import fcntl
flock_org = fcntl.flock


class CustomLockFactory(FileLock):

    @memoized_property
    def _module(self):

        def gevent_flock(fd, operation):
            """
            Gevent compatible flock
            """
            # set non-blocking, this will cause an exception if we cannot acquire a lock
            operation |= fcntl.LOCK_NB
            start_lock_time = time.time()
            timeout = 60 * 15  # 15min
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
                        log.error('Failed to acquire lock on `%s` after waiting %ss',
                                  self.filename, timeout)
                        raise
                    wait_timeout = 0.03
                    log.debug('Failed to acquire lock on `%s`, retry in %ss',
                              self.filename, wait_timeout)
                    gevent.sleep(wait_timeout)

        fcntl.flock = gevent_flock
        return fcntl


class FileNamespaceBackend(PickleSerializer, file_backend.DBMBackend):
    key_prefix = 'file_backend'

    def __init__(self, arguments):
        arguments['lock_factory'] = CustomLockFactory
        db_file = arguments.get('filename')

        log.debug('initialing %s DB in %s', self.__class__.__name__, db_file)
        try:
            super(FileNamespaceBackend, self).__init__(arguments)
        except Exception:
            log.error('Failed to initialize db at: %s', db_file)
            raise

    def __repr__(self):
        return '{} `{}`'.format(self.__class__, self.filename)

    def list_keys(self, prefix=''):
        prefix = '{}:{}'.format(self.key_prefix, prefix)

        def cond(v):
            if not prefix:
                return True

            if v.startswith(prefix):
                return True
            return False

        with self._dbm_file(True) as dbm:
            try:
                return filter(cond, dbm.keys())
            except Exception:
                log.error('Failed to fetch DBM keys from DB: %s', self.get_store())
                raise

    def get_store(self):
        return self.filename

    def _dbm_get(self, key):
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

    def get(self, key):
        try:
            return self._dbm_get(key)
        except Exception:
            log.error('Failed to fetch DBM key %s from DB: %s', key, self.get_store())
            raise

    def set(self, key, value):
        with self._dbm_file(True) as dbm:
            dbm[key] = self._dumps(value)

    def set_multi(self, mapping):
        with self._dbm_file(True) as dbm:
            for key, value in mapping.items():
                dbm[key] = self._dumps(value)


class BaseRedisBackend(redis_backend.RedisBackend):
    key_prefix = ''

    def __init__(self, arguments):
        super(BaseRedisBackend, self).__init__(arguments)
        self._lock_timeout = self.lock_timeout
        self._lock_auto_renewal = asbool(arguments.pop("lock_auto_renewal", True))

        if self._lock_auto_renewal and not self._lock_timeout:
            # set default timeout for auto_renewal
            self._lock_timeout = 30

    def _create_client(self):
        args = {}

        if self.url is not None:
            args.update(url=self.url)

        else:
            args.update(
                host=self.host, password=self.password,
                port=self.port, db=self.db
            )

        connection_pool = redis.ConnectionPool(**args)

        return redis.StrictRedis(connection_pool=connection_pool)

    def list_keys(self, prefix=''):
        prefix = '{}:{}*'.format(self.key_prefix, prefix)
        return self.client.keys(prefix)

    def get_store(self):
        return self.client.connection_pool

    def get(self, key):
        value = self.client.get(key)
        if value is None:
            return NO_VALUE
        return self._loads(value)

    def get_multi(self, keys):
        if not keys:
            return []
        values = self.client.mget(keys)
        loads = self._loads
        return [
            loads(v) if v is not None else NO_VALUE
            for v in values]

    def set(self, key, value):
        if self.redis_expiration_time:
            self.client.setex(key, self.redis_expiration_time,
                              self._dumps(value))
        else:
            self.client.set(key, self._dumps(value))

    def set_multi(self, mapping):
        dumps = self._dumps
        mapping = dict(
            (k, dumps(v))
            for k, v in mapping.items()
        )

        if not self.redis_expiration_time:
            self.client.mset(mapping)
        else:
            pipe = self.client.pipeline()
            for key, value in mapping.items():
                pipe.setex(key, self.redis_expiration_time, value)
            pipe.execute()

    def get_mutex(self, key):
        if self.distributed_lock:
            lock_key = redis_backend.u('_lock_{0}').format(key)
            return get_mutex_lock(self.client, lock_key, self._lock_timeout,
                                  auto_renewal=self._lock_auto_renewal)
        else:
            return None


class RedisPickleBackend(PickleSerializer, BaseRedisBackend):
    key_prefix = 'redis_pickle_backend'
    pass


class RedisMsgPackBackend(MsgPackSerializer, BaseRedisBackend):
    key_prefix = 'redis_msgpack_backend'
    pass


def get_mutex_lock(client, lock_key, lock_timeout, auto_renewal=False):
    import redis_lock

    class _RedisLockWrapper(object):
        """LockWrapper for redis_lock"""

        @classmethod
        def get_lock(cls):
            return redis_lock.Lock(
                redis_client=client,
                name=lock_key,
                expire=lock_timeout,
                auto_renewal=auto_renewal,
                strict=True,
            )

        def __repr__(self):
            return "{}:{}".format(self.__class__.__name__, lock_key)

        def __str__(self):
            return "{}:{}".format(self.__class__.__name__, lock_key)

        def __init__(self):
            self.lock = self.get_lock()
            self.lock_key = lock_key

        def acquire(self, wait=True):
            log.debug('Trying to acquire Redis lock for key %s', self.lock_key)
            try:
                acquired = self.lock.acquire(wait)
                log.debug('Got lock for key %s, %s', self.lock_key, acquired)
                return acquired
            except redis_lock.AlreadyAcquired:
                return False
            except redis_lock.AlreadyStarted:
                # refresh thread exists, but it also means we acquired the lock
                return True

        def release(self):
            try:
                self.lock.release()
            except redis_lock.NotAcquired:
                pass

    return _RedisLockWrapper()
