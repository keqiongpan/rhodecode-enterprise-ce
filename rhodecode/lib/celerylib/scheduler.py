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
import logging
import importlib

from celery.beat import (
    PersistentScheduler, ScheduleEntry as CeleryScheduleEntry)

log = logging.getLogger(__name__)


class FileScheduleEntry(CeleryScheduleEntry):
    def __init__(self, name=None, task=None, last_run_at=None,
                 total_run_count=None, schedule=None, args=(), kwargs=None,
                 options=None, relative=False, app=None, **_kwargs):
        kwargs = kwargs or {}
        options = options or {}

        # because our custom loader passes in some variables that the original
        # function doesn't expect, we have this thin wrapper

        super(FileScheduleEntry, self).__init__(
            name=name, task=task, last_run_at=last_run_at,
            total_run_count=total_run_count, schedule=schedule, args=args,
            kwargs=kwargs, options=options, relative=relative, app=app)


class FileScheduler(PersistentScheduler):
    """CE base scheduler"""
    Entry = FileScheduleEntry

    def setup_schedule(self):
        log.info("setup_schedule called")
        super(FileScheduler, self).setup_schedule()


try:
    # try if we have EE scheduler available
    module = importlib.import_module('rc_ee.lib.celerylib.scheduler')
    RcScheduler = module.RcScheduler
except ImportError:
    # fallback to CE scheduler
    RcScheduler = FileScheduler
