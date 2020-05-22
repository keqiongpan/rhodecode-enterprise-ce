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

import os
import atexit
import logging

log = logging.getLogger(__name__)

cache_keys_by_pid = []


@atexit.register
def free_cache_keys():
    ssh_cmd = os.environ.get('RC_CMD_SSH_WRAPPER')
    if ssh_cmd:
        return

    from rhodecode.model.db import Session, CacheKey
    log.info('Clearing %s cache keys', len(cache_keys_by_pid))

    if cache_keys_by_pid:
        try:
            for cache_key in cache_keys_by_pid:
                CacheKey.query().filter(CacheKey.cache_key == cache_key).delete()
            Session().commit()
        except Exception:
            log.warn('Failed to clear keys, exiting gracefully')
