# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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
import io
import re
import datetime
import logging
import Queue
import subprocess32
import os


from dateutil.parser import parse
from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request
from pyramid.interfaces import IRoutesMapper
from pyramid.settings import asbool
from pyramid.path import AssetResolver
from threading import Thread

from rhodecode.translation import _ as tsf
from rhodecode.config.jsroutes import generate_jsroutes_content
from rhodecode.lib import auth
from rhodecode.lib.base import get_auth_user


import rhodecode


log = logging.getLogger(__name__)


def add_renderer_globals(event):
    from rhodecode.lib import helpers

    # TODO: When executed in pyramid view context the request is not available
    # in the event. Find a better solution to get the request.
    request = event['request'] or get_current_request()

    # Add Pyramid translation as '_' to context
    event['_'] = request.translate
    event['_ungettext'] = request.plularize
    event['h'] = helpers


def add_localizer(event):
    request = event.request
    localizer = request.localizer

    def auto_translate(*args, **kwargs):
        return localizer.translate(tsf(*args, **kwargs))

    request.translate = auto_translate
    request.plularize = localizer.pluralize


def set_user_lang(event):
    request = event.request
    cur_user = getattr(request, 'user', None)

    if cur_user:
        user_lang = cur_user.get_instance().user_data.get('language')
        if user_lang:
            log.debug('lang: setting current user:%s language to: %s', cur_user, user_lang)
            event.request._LOCALE_ = user_lang


def add_request_user_context(event):
    """
    Adds auth user into request context
    """
    request = event.request
    # access req_id as soon as possible
    req_id = request.req_id

    if hasattr(request, 'vcs_call'):
        # skip vcs calls
        return

    if hasattr(request, 'rpc_method'):
        # skip api calls
        return

    auth_user = get_auth_user(request)
    request.user = auth_user
    request.environ['rc_auth_user'] = auth_user
    request.environ['rc_req_id'] = req_id

def inject_app_settings(event):
    settings = event.app.registry.settings
    # inject info about available permissions
    auth.set_available_permissions(settings)


def scan_repositories_if_enabled(event):
    """
    This is subscribed to the `pyramid.events.ApplicationCreated` event. It
    does a repository scan if enabled in the settings.
    """
    settings = event.app.registry.settings
    vcs_server_enabled = settings['vcs.server.enable']
    import_on_startup = settings['startup.import_repos']
    if vcs_server_enabled and import_on_startup:
        from rhodecode.model.scm import ScmModel
        from rhodecode.lib.utils import repo2db_mapper, get_rhodecode_base_path
        repositories = ScmModel().repo_scan(get_rhodecode_base_path())
        repo2db_mapper(repositories, remove_obsolete=False)


def write_metadata_if_needed(event):
    """
    Writes upgrade metadata
    """
    import rhodecode
    from rhodecode.lib import system_info
    from rhodecode.lib import ext_json

    fname = '.rcmetadata.json'
    ini_loc = os.path.dirname(rhodecode.CONFIG.get('__file__'))
    metadata_destination = os.path.join(ini_loc, fname)

    def get_update_age():
        now = datetime.datetime.utcnow()

        with open(metadata_destination, 'rb') as f:
            data = ext_json.json.loads(f.read())
            if 'created_on' in data:
                update_date = parse(data['created_on'])
                diff = now - update_date
                return diff.total_seconds() / 60.0

        return 0

    def write():
        configuration = system_info.SysInfo(
            system_info.rhodecode_config)()['value']
        license_token = configuration['config']['license_token']

        setup = dict(
            workers=configuration['config']['server:main'].get(
                'workers', '?'),
            worker_type=configuration['config']['server:main'].get(
                'worker_class', 'sync'),
        )
        dbinfo = system_info.SysInfo(system_info.database_info)()['value']
        del dbinfo['url']

        metadata = dict(
            desc='upgrade metadata info',
            license_token=license_token,
            created_on=datetime.datetime.utcnow().isoformat(),
            usage=system_info.SysInfo(system_info.usage_info)()['value'],
            platform=system_info.SysInfo(system_info.platform_type)()['value'],
            database=dbinfo,
            cpu=system_info.SysInfo(system_info.cpu)()['value'],
            memory=system_info.SysInfo(system_info.memory)()['value'],
            setup=setup
        )

        with open(metadata_destination, 'wb') as f:
            f.write(ext_json.json.dumps(metadata))

    settings = event.app.registry.settings
    if settings.get('metadata.skip'):
        return

    # only write this every 24h, workers restart caused unwanted delays
    try:
        age_in_min = get_update_age()
    except Exception:
        age_in_min = 0

    if age_in_min > 60 * 60 * 24:
        return

    try:
        write()
    except Exception:
        pass


def write_js_routes_if_enabled(event):
    registry = event.app.registry

    mapper = registry.queryUtility(IRoutesMapper)
    _argument_prog = re.compile('\{(.*?)\}|:\((.*)\)')

    def _extract_route_information(route):
        """
        Convert a route into tuple(name, path, args), eg:
            ('show_user', '/profile/%(username)s', ['username'])
        """

        routepath = route.pattern
        pattern = route.pattern

        def replace(matchobj):
            if matchobj.group(1):
                return "%%(%s)s" % matchobj.group(1).split(':')[0]
            else:
                return "%%(%s)s" % matchobj.group(2)

        routepath = _argument_prog.sub(replace, routepath)

        if not routepath.startswith('/'):
            routepath = '/'+routepath

        return (
            route.name,
            routepath,
            [(arg[0].split(':')[0] if arg[0] != '' else arg[1])
              for arg in _argument_prog.findall(pattern)]
        )

    def get_routes():
        # pyramid routes
        for route in mapper.get_routes():
            if not route.name.startswith('__'):
                yield _extract_route_information(route)

    if asbool(registry.settings.get('generate_js_files', 'false')):
        static_path = AssetResolver().resolve('rhodecode:public').abspath()
        jsroutes = get_routes()
        jsroutes_file_content = generate_jsroutes_content(jsroutes)
        jsroutes_file_path = os.path.join(
            static_path, 'js', 'rhodecode', 'routes.js')

        with io.open(jsroutes_file_path, 'w', encoding='utf-8') as f:
            f.write(jsroutes_file_content)


class Subscriber(object):
    """
    Base class for subscribers to the pyramid event system.
    """
    def __call__(self, event):
        self.run(event)

    def run(self, event):
        raise NotImplementedError('Subclass has to implement this.')


class AsyncSubscriber(Subscriber):
    """
    Subscriber that handles the execution of events in a separate task to not
    block the execution of the code which triggers the event. It puts the
    received events into a queue from which the worker process takes them in
    order.
    """
    def __init__(self):
        self._stop = False
        self._eventq = Queue.Queue()
        self._worker = self.create_worker()
        self._worker.start()

    def __call__(self, event):
        self._eventq.put(event)

    def create_worker(self):
        worker = Thread(target=self.do_work)
        worker.daemon = True
        return worker

    def stop_worker(self):
        self._stop = False
        self._eventq.put(None)
        self._worker.join()

    def do_work(self):
        while not self._stop:
            event = self._eventq.get()
            if event is not None:
                self.run(event)


class AsyncSubprocessSubscriber(AsyncSubscriber):
    """
    Subscriber that uses the subprocess32 module to execute a command if an
    event is received. Events are handled asynchronously.
    """

    def __init__(self, cmd, timeout=None):
        super(AsyncSubprocessSubscriber, self).__init__()
        self._cmd = cmd
        self._timeout = timeout

    def run(self, event):
        cmd = self._cmd
        timeout = self._timeout
        log.debug('Executing command %s.', cmd)

        try:
            output = subprocess32.check_output(
                cmd, timeout=timeout, stderr=subprocess32.STDOUT)
            log.debug('Command finished %s', cmd)
            if output:
                log.debug('Command output: %s', output)
        except subprocess32.TimeoutExpired as e:
            log.exception('Timeout while executing command.')
            if e.output:
                log.error('Command output: %s', e.output)
        except subprocess32.CalledProcessError as e:
            log.exception('Error while executing command.')
            if e.output:
                log.error('Command output: %s', e.output)
        except:
            log.exception(
                'Exception while executing command %s.', cmd)
