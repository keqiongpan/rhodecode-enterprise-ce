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
import pylons
import Queue
import subprocess32

from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request
from threading import Thread

from rhodecode.translation import _ as tsf


log = logging.getLogger(__name__)


def add_renderer_globals(event):
    # Put pylons stuff into the context. This will be removed as soon as
    # migration to pyramid is finished.
    conf = pylons.config._current_obj()
    event['h'] = conf.get('pylons.h')
    event['c'] = pylons.tmpl_context
    event['url'] = pylons.url

    # TODO: When executed in pyramid view context the request is not available
    # in the event. Find a better solution to get the request.
    request = event['request'] or get_current_request()

    # Add Pyramid translation as '_' to context
    event['_'] = request.translate
    event['localizer'] = request.localizer


def add_localizer(event):
    request = event.request
    localizer = get_localizer(request)

    def auto_translate(*args, **kwargs):
        return localizer.translate(tsf(*args, **kwargs))

    request.localizer = localizer
    request.translate = auto_translate


def scan_repositories_if_enabled(event):
    """
    This is subscribed to the `pyramid.events.ApplicationCreated` event. It
    does a repository scan if enabled in the settings.
    """
    from rhodecode.model.scm import ScmModel
    from rhodecode.lib.utils import repo2db_mapper, get_rhodecode_base_path
    settings = event.app.registry.settings
    vcs_server_enabled = settings['vcs.server.enable']
    import_on_startup = settings['startup.import_repos']
    if vcs_server_enabled and import_on_startup:
        repositories = ScmModel().repo_scan(get_rhodecode_base_path())
        repo2db_mapper(repositories, remove_obsolete=False)


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
