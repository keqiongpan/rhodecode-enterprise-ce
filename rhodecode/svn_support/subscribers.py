# -*- coding: utf-8 -*-

# Copyright (C) 2016-2016  RhodeCode GmbH
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
import Queue
import subprocess32
from threading import Thread


from .utils import generate_mod_dav_svn_config


log = logging.getLogger(__name__)


def generate_config_subscriber(event):
    """
    Subscriber to the `rhodcode.events.RepoGroupEvent`. This triggers the
    automatic generation of mod_dav_svn config file on repository group
    changes.
    """
    try:
        generate_mod_dav_svn_config(event.request.registry)
    except Exception:
        log.exception(
            'Exception while generating subversion mod_dav_svn configuration.')


class Subscriber(object):
    def __call__(self, event):
        self.run(event)

    def run(self, event):
        raise NotImplementedError('Subclass has to implement this.')


class AsyncSubscriber(Subscriber):
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
