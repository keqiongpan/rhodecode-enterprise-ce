# -*- coding: utf-8 -*-

# Copyright (C) 2016-2018 RhodeCode GmbH
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

import pytest

from rhodecode.lib import rc_cache


@pytest.mark.usefixtures( 'app')
class TestCaches(object):

    def test_cache_decorator_init_not_configured(self):
        with pytest.raises(EnvironmentError):
            rc_cache.get_or_create_region('dontexist')

    @pytest.mark.parametrize('region_name', [
        'cache_perms', u'cache_perms',
    ])
    def test_cache_decorator_init(self, region_name):
        namespace = region_name
        cache_region = rc_cache.get_or_create_region(
            region_name, region_namespace=namespace)
        assert cache_region

    @pytest.mark.parametrize('example_input', [
        ('',),
        (u'/ac',),
        (u'/ac', 1, 2, object()),
        (u'/ęćc', 1, 2, object()),
        ('/ąac',),
        (u'/ac', ),
    ])
    def test_cache_manager_create_key(self, example_input):
        key = rc_cache.utils.compute_key_from_params(*example_input)
        assert key

    @pytest.mark.parametrize('example_namespace', [
        'namespace', None
    ])
    @pytest.mark.parametrize('example_input', [
        ('',),
        (u'/ac',),
        (u'/ac', 1, 2, object()),
        (u'/ęćc', 1, 2, object()),
        ('/ąac',),
        (u'/ac', ),
    ])
    def test_cache_keygen(self, example_input, example_namespace):
        def func_wrapped():
            return 1
        func = rc_cache.utils.key_generator(example_namespace, func_wrapped)
        key = func(*example_input)
        assert key

    def test_store_value_in_cache(self):
        cache_region = rc_cache.get_or_create_region('cache_perms')
        # make sure we empty the cache now
        cache_region.delete_multi(cache_region.backend.list_keys())

        assert cache_region.backend.list_keys() == []

        @cache_region.conditional_cache_on_arguments(expiration_time=5)
        def compute(key):
            return time.time()

        for x in range(10):
            compute(x)

        assert len(set(cache_region.backend.list_keys())) == 10

    def test_store_and_get_value_from_region(self):
        cache_region = rc_cache.get_or_create_region('cache_perms')
        # make sure we empty the cache now
        for key in cache_region.backend.list_keys():
            cache_region.delete(key)
        assert cache_region.backend.list_keys() == []

        @cache_region.conditional_cache_on_arguments(expiration_time=5)
        def compute(key):
            return time.time()

        result = set()
        for x in range(10):
            ret = compute('x')
            result.add(ret)

        # once computed we have only one value (the same from cache)
        # after executing it 10x
        assert len(result) == 1
