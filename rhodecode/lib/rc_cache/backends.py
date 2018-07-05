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

from dogpile.cache.backends import memory as memory_backend
from dogpile.cache.backends import file as file_backend
from dogpile.cache.backends import redis as redis_backend
from dogpile.cache.backends.file import NO_VALUE, compat

from rhodecode.lib.memory_lru_debug import LRUDict

_default_max_size = 1024


class LRUMemoryBackend(memory_backend.MemoryBackend):

    def __init__(self, arguments):
        max_size = arguments.pop('max_size', _default_max_size)
        arguments['cache_dict'] = LRUDict(max_size)
        super(LRUMemoryBackend, self).__init__(arguments)


class Serializer(object):
    def _dumps(self, value):
        return compat.pickle.dumps(value)

    def _loads(self, value):
        return compat.pickle.loads(value)


class FileNamespaceBackend(Serializer, file_backend.DBMBackend):

    def __init__(self, arguments):
        super(FileNamespaceBackend, self).__init__(arguments)

    def list_keys(self):
        with self._dbm_file(True) as dbm:
            return dbm.keys()

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
    def list_keys(self):
        return self.client.keys()

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
