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
import functools

import beaker
import logging
import threading

from beaker.cache import _cache_decorate, region_invalidate
from sqlalchemy.exc import IntegrityError

from rhodecode.lib.utils import safe_str, sha1
from rhodecode.model.db import Session, CacheKey

log = logging.getLogger(__name__)


DEFAULT_CACHE_MANAGER_CONFIG = {
    'type': 'memorylru_base',
    'max_items': 10240,
    'key_length': 256,
    'enabled': True
}


def get_default_cache_settings(settings):
    cache_settings = {}
    for key in settings.keys():
        for prefix in ['beaker.cache.', 'cache.']:
            if key.startswith(prefix):
                name = key.split(prefix)[1].strip()
                cache_settings[name] = settings[key].strip()
    return cache_settings


# set cache regions for beaker so celery can utilise it
def configure_caches(settings, default_region_settings=None):
    cache_settings = {'regions': None}
    # main cache settings used as default ...
    cache_settings.update(get_default_cache_settings(settings))
    default_region_settings = default_region_settings or \
                              {'type': DEFAULT_CACHE_MANAGER_CONFIG['type']}
    if cache_settings['regions']:
        for region in cache_settings['regions'].split(','):
            region = region.strip()
            region_settings = default_region_settings.copy()
            for key, value in cache_settings.items():
                if key.startswith(region):
                    region_settings[key.split(region + '.')[-1]] = value
            log.debug('Configuring cache region `%s` with settings %s',
                      region, region_settings)
            configure_cache_region(
                region, region_settings, cache_settings)


def configure_cache_region(
        region_name, region_settings, default_cache_kw, default_expire=60):
    default_type = default_cache_kw.get('type', 'memory')
    default_lock_dir = default_cache_kw.get('lock_dir')
    default_data_dir = default_cache_kw.get('data_dir')

    region_settings['lock_dir'] = region_settings.get('lock_dir', default_lock_dir)
    region_settings['data_dir'] = region_settings.get('data_dir', default_data_dir)
    region_settings['type'] = region_settings.get('type', default_type)
    region_settings['expire'] = int(region_settings.get('expire', default_expire))

    beaker.cache.cache_regions[region_name] = region_settings


def compute_key_from_params(*args):
    """
    Helper to compute key from given params to be used in cache manager
    """
    return sha1("_".join(map(safe_str, args)))


def get_repo_namespace_key(prefix, repo_name):
    return '{0}_{1}'.format(prefix, compute_key_from_params(repo_name))


class ActiveRegionCache(object):
    def __init__(self, context):
        self.context = context

    def invalidate(self, *args, **kwargs):
        return False

    def compute(self):
        log.debug('Context cache: getting obj %s from cache', self.context)
        return self.context.compute_func(self.context.cache_key)


class FreshRegionCache(ActiveRegionCache):
    def invalidate(self):
        log.debug('Context cache: invalidating cache for %s', self.context)
        region_invalidate(
            self.context.compute_func, None, self.context.cache_key)
        return True


class InvalidationContext(object):
    def __repr__(self):
        return '<InvalidationContext:{}[{}]>'.format(
            safe_str(self.repo_name), safe_str(self.cache_type))

    def __init__(self, compute_func, repo_name, cache_type,
                 raise_exception=False, thread_scoped=False):
        self.compute_func = compute_func
        self.repo_name = repo_name
        self.cache_type = cache_type
        self.cache_key = compute_key_from_params(
            repo_name, cache_type)
        self.raise_exception = raise_exception

        # Append the thread id to the cache key if this invalidation context
        # should be scoped to the current thread.
        if thread_scoped:
            thread_id = threading.current_thread().ident
            self.cache_key = '{cache_key}_{thread_id}'.format(
                cache_key=self.cache_key, thread_id=thread_id)

    def get_cache_obj(self):
        cache_key = CacheKey.get_cache_key(
            self.repo_name, self.cache_type)
        cache_obj = CacheKey.get_active_cache(cache_key)
        if not cache_obj:
            cache_obj = CacheKey(cache_key, self.repo_name)
        return cache_obj

    def __enter__(self):
        """
        Test if current object is valid, and return CacheRegion function
        that does invalidation and calculation
        """

        self.cache_obj = self.get_cache_obj()
        if self.cache_obj.cache_active:
            # means our cache obj is existing and marked as it's
            # cache is not outdated, we return BaseInvalidator
            self.skip_cache_active_change = True
            return ActiveRegionCache(self)

        # the key is either not existing or set to False, we return
        # the real invalidator which re-computes value. We additionally set
        # the flag to actually update the Database objects
        self.skip_cache_active_change = False
        return FreshRegionCache(self)

    def __exit__(self, exc_type, exc_val, exc_tb):

        if self.skip_cache_active_change:
            return

        try:
            self.cache_obj.cache_active = True
            Session().add(self.cache_obj)
            Session().commit()
        except IntegrityError:
            # if we catch integrity error, it means we inserted this object
            # assumption is that's really an edge race-condition case and
            # it's safe is to skip it
            Session().rollback()
        except Exception:
            log.exception('Failed to commit on cache key update')
            Session().rollback()
            if self.raise_exception:
                raise


def includeme(config):
    configure_caches(config.registry.settings)
