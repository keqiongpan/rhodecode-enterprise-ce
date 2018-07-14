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
import os
import logging
import functools

from dogpile.cache import CacheRegion
from dogpile.cache.util import compat

from rhodecode.lib.utils import safe_str, sha1
from . import region_meta

log = logging.getLogger(__name__)


class RhodeCodeCacheRegion(CacheRegion):

    def conditional_cache_on_arguments(
            self, namespace=None,
            expiration_time=None,
            should_cache_fn=None,
            to_str=compat.string_type,
            function_key_generator=None,
            condition=True):
        """
        Custom conditional decorator, that will not touch any dogpile internals if
        condition isn't meet. This works a bit different than should_cache_fn
        And it's faster in cases we don't ever want to compute cached values
        """
        expiration_time_is_callable = compat.callable(expiration_time)

        if function_key_generator is None:
            function_key_generator = self.function_key_generator

        def decorator(fn):
            if to_str is compat.string_type:
                # backwards compatible
                key_generator = function_key_generator(namespace, fn)
            else:
                key_generator = function_key_generator(namespace, fn, to_str=to_str)

            @functools.wraps(fn)
            def decorate(*arg, **kw):
                key = key_generator(*arg, **kw)

                @functools.wraps(fn)
                def creator():
                    return fn(*arg, **kw)

                if not condition:
                    return creator()

                timeout = expiration_time() if expiration_time_is_callable \
                    else expiration_time

                return self.get_or_create(key, creator, timeout, should_cache_fn)

            def invalidate(*arg, **kw):
                key = key_generator(*arg, **kw)
                self.delete(key)

            def set_(value, *arg, **kw):
                key = key_generator(*arg, **kw)
                self.set(key, value)

            def get(*arg, **kw):
                key = key_generator(*arg, **kw)
                return self.get(key)

            def refresh(*arg, **kw):
                key = key_generator(*arg, **kw)
                value = fn(*arg, **kw)
                self.set(key, value)
                return value

            decorate.set = set_
            decorate.invalidate = invalidate
            decorate.refresh = refresh
            decorate.get = get
            decorate.original = fn
            decorate.key_generator = key_generator

            return decorate

        return decorator


def make_region(*arg, **kw):
    return RhodeCodeCacheRegion(*arg, **kw)


def get_default_cache_settings(settings, prefixes=None):
    prefixes = prefixes or []
    cache_settings = {}
    for key in settings.keys():
        for prefix in prefixes:
            if key.startswith(prefix):
                name = key.split(prefix)[1].strip()
                val = settings[key]
                if isinstance(val, basestring):
                    val = val.strip()
                cache_settings[name] = val
    return cache_settings


def compute_key_from_params(*args):
    """
    Helper to compute key from given params to be used in cache manager
    """
    return sha1("_".join(map(safe_str, args)))


def key_generator(namespace, fn):
    fname = fn.__name__

    def generate_key(*args):
        namespace_pref = namespace or 'default'
        arg_key = compute_key_from_params(*args)
        final_key = "{}:{}_{}".format(namespace_pref, fname, arg_key)

        return final_key

    return generate_key


def get_or_create_region(region_name, region_namespace=None):
    from rhodecode.lib.rc_cache.backends import FileNamespaceBackend
    region_obj = region_meta.dogpile_cache_regions.get(region_name)
    if not region_obj:
        raise EnvironmentError(
            'Region `{}` not in configured: {}.'.format(
                region_name, region_meta.dogpile_cache_regions.keys()))

    region_uid_name = '{}:{}'.format(region_name, region_namespace)
    if isinstance(region_obj.actual_backend, FileNamespaceBackend):
        region_exist = region_meta.dogpile_cache_regions.get(region_namespace)
        if region_exist:
            log.debug('Using already configured region: %s', region_namespace)
            return region_exist
        cache_dir = region_meta.dogpile_config_defaults['cache_dir']
        expiration_time = region_obj.expiration_time

        if not os.path.isdir(cache_dir):
            os.makedirs(cache_dir)
        new_region = make_region(
            name=region_uid_name, function_key_generator=key_generator
        )
        namespace_filename = os.path.join(
            cache_dir, "{}.cache.dbm".format(region_namespace))
        # special type that allows 1db per namespace
        new_region.configure(
            backend='dogpile.cache.rc.file_namespace',
            expiration_time=expiration_time,
            arguments={"filename": namespace_filename}
        )

        # create and save in region caches
        log.debug('configuring new region: %s',region_uid_name)
        region_obj = region_meta.dogpile_cache_regions[region_namespace] = new_region

    return region_obj


def clear_cache_namespace(cache_region, cache_namespace_uid):
    region = get_or_create_region(cache_region, cache_namespace_uid)
    cache_keys = region.backend.list_keys(prefix=cache_namespace_uid)
    region.delete_multi(cache_keys)
    return len(cache_keys)
