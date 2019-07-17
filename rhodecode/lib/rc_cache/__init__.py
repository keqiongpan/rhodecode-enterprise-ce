# -*- coding: utf-8 -*-

# Copyright (C) 2015-2019 RhodeCode GmbH
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
from dogpile.cache import register_backend

register_backend(
    "dogpile.cache.rc.memory_lru", "rhodecode.lib.rc_cache.backends",
    "LRUMemoryBackend")

register_backend(
    "dogpile.cache.rc.file_namespace", "rhodecode.lib.rc_cache.backends",
    "FileNamespaceBackend")

register_backend(
    "dogpile.cache.rc.redis", "rhodecode.lib.rc_cache.backends",
    "RedisPickleBackend")

register_backend(
    "dogpile.cache.rc.redis_msgpack", "rhodecode.lib.rc_cache.backends",
    "RedisMsgPackBackend")


log = logging.getLogger(__name__)

from . import region_meta
from .utils import (
    get_default_cache_settings, backend_key_generator, get_or_create_region,
    clear_cache_namespace, make_region, InvalidationContext,
    FreshRegionCache, ActiveRegionCache)


def configure_dogpile_cache(settings):
    cache_dir = settings.get('cache_dir')
    if cache_dir:
        region_meta.dogpile_config_defaults['cache_dir'] = cache_dir

    rc_cache_data = get_default_cache_settings(settings, prefixes=['rc_cache.'])

    # inspect available namespaces
    avail_regions = set()
    for key in rc_cache_data.keys():
        namespace_name = key.split('.', 1)[0]
        avail_regions.add(namespace_name)
    log.debug('dogpile: found following cache regions: %s', avail_regions)

    # register them into namespace
    for region_name in avail_regions:
        new_region = make_region(
            name=region_name,
            function_key_generator=None
        )

        new_region.configure_from_config(settings, 'rc_cache.{}.'.format(region_name))
        new_region.function_key_generator = backend_key_generator(new_region.actual_backend)
        log.debug('dogpile: registering a new region %s[%s]', region_name, new_region.__dict__)
        region_meta.dogpile_cache_regions[region_name] = new_region


def includeme(config):
    configure_dogpile_cache(config.registry.settings)
