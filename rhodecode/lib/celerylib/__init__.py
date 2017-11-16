# -*- coding: utf-8 -*-

# Copyright (C) 2010-2017 RhodeCode GmbH
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

import socket
import logging

import rhodecode
from zope.cachedescriptors.property import Lazy as LazyProperty
from rhodecode.lib.celerylib.loader import (
    celery_app, RequestContextTask, get_logger)

async_task = celery_app.task


log = logging.getLogger(__name__)


class ResultWrapper(object):
    def __init__(self, task):
        self.task = task

    @LazyProperty
    def result(self):
        return self.task


def run_task(task, *args, **kwargs):
    if rhodecode.CELERY_ENABLED:
        celery_is_up = False
        try:
            t = task.apply_async(args=args, kwargs=kwargs)
            celery_is_up = True
            log.debug('executing task %s:%s in async mode', t.task_id, task)
            return t

        except socket.error as e:
            if isinstance(e, IOError) and e.errno == 111:
                log.error('Unable to connect to celeryd. Sync execution')
            else:
                log.exception("Exception while connecting to celeryd.")
        except KeyError as e:
            log.error('Unable to connect to celeryd. Sync execution')
        except Exception as e:
            log.exception(
                "Exception while trying to run task asynchronous. "
                "Fallback to sync execution.")

        # keep in mind there maybe a subtle race condition where something
        # depending on rhodecode.CELERY_ENABLED
        # will see CELERY_ENABLED as True before this has a chance to set False
        rhodecode.CELERY_ENABLED = celery_is_up
    else:
        log.debug('executing task %s:%s in sync mode', 'TASK', task)

    return ResultWrapper(task(*args, **kwargs))
