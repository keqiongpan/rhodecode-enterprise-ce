# -*- coding: utf-8 -*-

# Copyright (C) 2010-2019 RhodeCode GmbH
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
import json
import logging
import datetime
import time

from functools import partial

from pyramid.compat import configparser
from celery.result import AsyncResult
import celery.loaders.base
import celery.schedules

log = logging.getLogger(__name__)


def get_task_id(task):
    task_id = None
    if isinstance(task, AsyncResult):
        task_id = task.task_id

    return task_id


def crontab(value):
    return celery.schedules.crontab(**value)


def timedelta(value):
    return datetime.timedelta(**value)


def safe_json(get, section, key):
    value = ''
    try:
        value = get(key)
        json_value = json.loads(value)
    except ValueError:
        msg = 'The %s=%s is not valid json in section %s' % (
            key, value, section
        )
        raise ValueError(msg)

    return json_value


def raw_2_schedule(schedule_value, schedule_type):
    schedule_type_map = {
        'crontab': crontab,
        'timedelta': timedelta,
        'integer': int
    }
    scheduler_cls = schedule_type_map.get(schedule_type)

    if scheduler_cls is None:
        raise ValueError(
            'schedule type %s in section is invalid' % (
                schedule_type,
            )
        )
    try:
        schedule = scheduler_cls(schedule_value)
    except TypeError:
        log.exception('Failed to compose a schedule from value: %r', schedule_value)
        schedule = None
    return schedule


def get_beat_config(parser, section):

    get = partial(parser.get, section)
    has_option = partial(parser.has_option, section)

    schedule_type = get('type')
    schedule_value = safe_json(get, section, 'schedule')

    config = {
        'schedule_type': schedule_type,
        'schedule_value': schedule_value,
        'task': get('task'),
    }
    schedule = raw_2_schedule(schedule_value, schedule_type)
    if schedule:
        config['schedule'] = schedule

    if has_option('args'):
        config['args'] = safe_json(get, section, 'args')

    if has_option('kwargs'):
        config['kwargs'] = safe_json(get, section, 'kwargs')

    if has_option('force_update'):
        config['force_update'] = get('force_update')

    return config


def get_ini_config(ini_location):
    """
    Converts basic ini configuration into celery 4.X options
    """
    def key_converter(key_name):
        pref = 'celery.'
        if key_name.startswith(pref):
            return key_name[len(pref):].replace('.', '_').lower()

    def type_converter(parsed_key, value):
        # cast to int
        if value.isdigit():
            return int(value)

        # cast to bool
        if value.lower() in ['true', 'false', 'True', 'False']:
            return value.lower() == 'true'
        return value

    parser = configparser.SafeConfigParser(
        defaults={'here': os.path.abspath(ini_location)})
    parser.read(ini_location)

    ini_config = {}
    for k, v in parser.items('app:main'):
        pref = 'celery.'
        if k.startswith(pref):
            ini_config[key_converter(k)] = type_converter(key_converter(k), v)

    beat_config = {}
    for section in parser.sections():
        if section.startswith('celerybeat:'):
            name = section.split(':', 1)[1]
            beat_config[name] = get_beat_config(parser, section)

    # final compose of settings
    celery_settings = {}

    if ini_config:
        celery_settings.update(ini_config)
    if beat_config:
        celery_settings.update({'beat_schedule': beat_config})

    return celery_settings


def parse_ini_vars(ini_vars):
    options = {}
    for pairs in ini_vars.split(','):
        key, value = pairs.split('=')
        options[key] = value
    return options


def ping_db():
    from rhodecode.model import meta
    from rhodecode.model.db import DbMigrateVersion
    log.info('Testing DB connection...')

    for test in range(10):
        try:
            scalar = DbMigrateVersion.query().scalar()
            log.debug('DB PING %s@%s', scalar, scalar.version)
            break
        except Exception:
            retry = 1
            log.debug('DB not ready, next try in %ss', retry)
            time.sleep(retry)
        finally:
            meta.Session.remove()
