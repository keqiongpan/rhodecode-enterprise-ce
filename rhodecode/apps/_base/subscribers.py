# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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

from rhodecode import events
from rhodecode.lib import rc_cache

log = logging.getLogger(__name__)

# names of namespaces used for different permission related cached
# during flush operation we need to take care of all those
cache_namespaces = [
    'cache_user_auth.{}',
    'cache_user_repo_acl_ids.{}',
    'cache_user_user_group_acl_ids.{}',
    'cache_user_repo_group_acl_ids.{}'
]


def trigger_user_permission_flush(event):
    """
    Subscriber to the `UserPermissionsChange`. This triggers the
    automatic flush of permission caches, so the users affected receive new permissions
    Right Away
    """
    invalidate = True
    affected_user_ids = set(event.user_ids)
    for user_id in affected_user_ids:
        for cache_namespace_uid_tmpl in cache_namespaces:
            cache_namespace_uid = cache_namespace_uid_tmpl.format(user_id)
            del_keys = rc_cache.clear_cache_namespace(
                'cache_perms', cache_namespace_uid, invalidate=invalidate)
            log.debug('Invalidated %s cache keys for user_id: %s and namespace %s',
                      del_keys, user_id, cache_namespace_uid)


def includeme(config):
    config.add_subscriber(trigger_user_permission_flush, events.UserPermissionsChange)
