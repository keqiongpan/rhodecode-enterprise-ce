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
"""
Celery loader, run with::

    celery worker \
        --beat \
        --app rhodecode.lib.celerylib.loader \
        --scheduler rhodecode.lib.celerylib.scheduler.RcScheduler \
        --loglevel DEBUG --ini=._dev/dev.ini
"""
import os
import logging

from celery import Celery
from celery import signals
from celery import Task
from celery import exceptions  # noqa
from kombu.serialization import register
from pyramid.threadlocal import get_current_request

import rhodecode

from rhodecode.lib.auth import AuthUser
from rhodecode.lib.celerylib.utils import get_ini_config, parse_ini_vars
from rhodecode.lib.ext_json import json
from rhodecode.lib.pyramid_utils import bootstrap, setup_logging, prepare_request
from rhodecode.lib.utils2 import str2bool
from rhodecode.model import meta


register('json_ext', json.dumps, json.loads,
         content_type='application/x-json-ext',
         content_encoding='utf-8')

log = logging.getLogger('celery.rhodecode.loader')


def add_preload_arguments(parser):
    parser.add_argument(
        '--ini', default=None,
        help='Path to ini configuration file.'
    )
    parser.add_argument(
        '--ini-var', default=None,
        help='Comma separated list of key=value to pass to ini.'
    )


def get_logger(obj):
    custom_log = logging.getLogger(
        'rhodecode.task.{}'.format(obj.__class__.__name__))

    if rhodecode.CELERY_ENABLED:
        try:
            custom_log = obj.get_logger()
        except Exception:
            pass

    return custom_log


base_celery_config = {
    'result_backend': 'rpc://',
    'result_expires': 60 * 60 * 24,
    'result_persistent': True,
    'imports': [],
    'worker_max_tasks_per_child': 100,
    'accept_content': ['json_ext'],
    'task_serializer': 'json_ext',
    'result_serializer': 'json_ext',
    'worker_hijack_root_logger': False,
    'database_table_names': {
        'task': 'beat_taskmeta',
        'group': 'beat_groupmeta',
    }
}
# init main celery app
celery_app = Celery()
celery_app.user_options['preload'].add(add_preload_arguments)
ini_file_glob = None


@signals.setup_logging.connect
def setup_logging_callback(**kwargs):
    setup_logging(ini_file_glob)


@signals.user_preload_options.connect
def on_preload_parsed(options, **kwargs):
    ini_location = options['ini']
    ini_vars = options['ini_var']
    celery_app.conf['INI_PYRAMID'] = options['ini']

    if ini_location is None:
        print('You must provide the paste --ini argument')
        exit(-1)

    options = None
    if ini_vars is not None:
        options = parse_ini_vars(ini_vars)

    global ini_file_glob
    ini_file_glob = ini_location

    log.debug('Bootstrapping RhodeCode application...')
    env = bootstrap(ini_location, options=options)

    setup_celery_app(
        app=env['app'], root=env['root'], request=env['request'],
        registry=env['registry'], closer=env['closer'],
        ini_location=ini_location)

    # fix the global flag even if it's disabled via .ini file because this
    # is a worker code that doesn't need this to be disabled.
    rhodecode.CELERY_ENABLED = True


@signals.task_success.connect
def task_success_signal(result, **kwargs):
    meta.Session.commit()
    closer = celery_app.conf['PYRAMID_CLOSER']
    if closer:
        closer()


@signals.task_retry.connect
def task_retry_signal(
        request, reason, einfo, **kwargs):
    meta.Session.remove()
    closer = celery_app.conf['PYRAMID_CLOSER']
    if closer:
        closer()


@signals.task_failure.connect
def task_failure_signal(
        task_id, exception, args, kwargs, traceback, einfo, **kargs):
    meta.Session.remove()
    closer = celery_app.conf['PYRAMID_CLOSER']
    if closer:
        closer()


@signals.task_revoked.connect
def task_revoked_signal(
        request, terminated, signum, expired, **kwargs):
    closer = celery_app.conf['PYRAMID_CLOSER']
    if closer:
        closer()


def setup_celery_app(app, root, request, registry, closer, ini_location):
    ini_dir = os.path.dirname(os.path.abspath(ini_location))
    celery_config = base_celery_config
    celery_config.update({
        # store celerybeat scheduler db where the .ini file is
        'beat_schedule_filename': os.path.join(ini_dir, 'celerybeat-schedule'),
    })
    ini_settings = get_ini_config(ini_location)
    log.debug('Got custom celery conf: %s', ini_settings)

    celery_config.update(ini_settings)
    celery_app.config_from_object(celery_config)

    celery_app.conf.update({'PYRAMID_APP': app})
    celery_app.conf.update({'PYRAMID_ROOT': root})
    celery_app.conf.update({'PYRAMID_REQUEST': request})
    celery_app.conf.update({'PYRAMID_REGISTRY': registry})
    celery_app.conf.update({'PYRAMID_CLOSER': closer})


def configure_celery(config, ini_location):
    """
    Helper that is called from our application creation logic. It gives
    connection info into running webapp and allows execution of tasks from
    RhodeCode itself
    """
    # store some globals into rhodecode
    rhodecode.CELERY_ENABLED = str2bool(
        config.registry.settings.get('use_celery'))
    if rhodecode.CELERY_ENABLED:
        log.info('Configuring celery based on `%s` file', ini_location)
        setup_celery_app(
            app=None, root=None, request=None, registry=config.registry,
            closer=None, ini_location=ini_location)


def maybe_prepare_env(req):
    environ = {}
    try:
        environ.update({
            'PATH_INFO': req.environ['PATH_INFO'],
            'SCRIPT_NAME': req.environ['SCRIPT_NAME'],
            'HTTP_HOST':
                req.environ.get('HTTP_HOST', req.environ['SERVER_NAME']),
            'SERVER_NAME': req.environ['SERVER_NAME'],
            'SERVER_PORT': req.environ['SERVER_PORT'],
            'wsgi.url_scheme': req.environ['wsgi.url_scheme'],
        })
    except Exception:
        pass

    return environ


class RequestContextTask(Task):
    """
    This is a celery task which will create a rhodecode app instance context
    for the task, patch pyramid with the original request
    that created the task and also add the user to the context.
    """

    def apply_async(self, args=None, kwargs=None, task_id=None, producer=None,
                    link=None, link_error=None, shadow=None, **options):
        """ queue the job to run (we are in web request context here) """

        req = get_current_request()

        # web case
        if hasattr(req, 'user'):
            ip_addr = req.user.ip_addr
            user_id = req.user.user_id

        # api case
        elif hasattr(req, 'rpc_user'):
            ip_addr = req.rpc_user.ip_addr
            user_id = req.rpc_user.user_id
        else:
            raise Exception(
                'Unable to fetch required data from request: {}. \n'
                'This task is required to be executed from context of '
                'request in a webapp'.format(repr(req)))

        if req:
            # we hook into kwargs since it is the only way to pass our data to
            # the celery worker
            environ = maybe_prepare_env(req)
            options['headers'] = options.get('headers', {})
            options['headers'].update({
                'rhodecode_proxy_data': {
                    'environ': environ,
                    'auth_user': {
                        'ip_addr': ip_addr,
                        'user_id': user_id
                    },
                }
            })

        return super(RequestContextTask, self).apply_async(
            args, kwargs, task_id, producer, link, link_error, shadow, **options)

    def __call__(self, *args, **kwargs):
        """ rebuild the context and then run task on celery worker """

        proxy_data = getattr(self.request, 'rhodecode_proxy_data', None)
        if not proxy_data:
            return super(RequestContextTask, self).__call__(*args, **kwargs)

        log.debug('using celery proxy data to run task: %r', proxy_data)
        # re-inject and register threadlocals for proper routing support
        request = prepare_request(proxy_data['environ'])
        request.user = AuthUser(user_id=proxy_data['auth_user']['user_id'],
                                ip_addr=proxy_data['auth_user']['ip_addr'])

        return super(RequestContextTask, self).__call__(*args, **kwargs)

