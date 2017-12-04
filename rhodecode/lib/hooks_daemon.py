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

import json
import logging
import traceback
import threading
from BaseHTTPServer import BaseHTTPRequestHandler
from SocketServer import TCPServer

import rhodecode
from rhodecode.model import meta
from rhodecode.lib.base import bootstrap_request, bootstrap_config
from rhodecode.lib import hooks_base
from rhodecode.lib.utils2 import AttributeDict


log = logging.getLogger(__name__)


class HooksHttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        method, extras = self._read_request()
        try:
            result = self._call_hook(method, extras)
        except Exception as e:
            exc_tb = traceback.format_exc()
            result = {
                'exception': e.__class__.__name__,
                'exception_traceback': exc_tb,
                'exception_args': e.args
            }
        self._write_response(result)

    def _read_request(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length).decode('utf-8')
        data = json.loads(body)
        return data['method'], data['extras']

    def _write_response(self, result):
        self.send_response(200)
        self.send_header("Content-type", "text/json")
        self.end_headers()
        self.wfile.write(json.dumps(result))

    def _call_hook(self, method, extras):
        hooks = Hooks()
        try:
            result = getattr(hooks, method)(extras)
        finally:
            meta.Session.remove()
        return result

    def log_message(self, format, *args):
        """
        This is an overridden method of BaseHTTPRequestHandler which logs using
        logging library instead of writing directly to stderr.
        """

        message = format % args

        # TODO: mikhail: add different log levels support
        log.debug(
            "%s - - [%s] %s", self.client_address[0],
            self.log_date_time_string(), message)


class DummyHooksCallbackDaemon(object):
    def __init__(self):
        self.hooks_module = Hooks.__module__

    def __enter__(self):
        log.debug('Running dummy hooks callback daemon')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        log.debug('Exiting dummy hooks callback daemon')


class ThreadedHookCallbackDaemon(object):

    _callback_thread = None
    _daemon = None
    _done = False

    def __init__(self):
        self._prepare()

    def __enter__(self):
        self._run()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        log.debug('Callback daemon exiting now...')
        self._stop()

    def _prepare(self):
        raise NotImplementedError()

    def _run(self):
        raise NotImplementedError()

    def _stop(self):
        raise NotImplementedError()


class HttpHooksCallbackDaemon(ThreadedHookCallbackDaemon):
    """
    Context manager which will run a callback daemon in a background thread.
    """

    hooks_uri = None

    IP_ADDRESS = '127.0.0.1'

    # From Python docs: Polling reduces our responsiveness to a shutdown
    # request and wastes cpu at all other times.
    POLL_INTERVAL = 0.01

    def _prepare(self):
        log.debug("Preparing HTTP callback daemon and registering hook object")

        self._done = False
        self._daemon = TCPServer((self.IP_ADDRESS, 0), HooksHttpHandler)
        _, port = self._daemon.server_address
        self.hooks_uri = '{}:{}'.format(self.IP_ADDRESS, port)

        log.debug("Hooks uri is: %s", self.hooks_uri)

    def _run(self):
        log.debug("Running event loop of callback daemon in background thread")
        callback_thread = threading.Thread(
            target=self._daemon.serve_forever,
            kwargs={'poll_interval': self.POLL_INTERVAL})
        callback_thread.daemon = True
        callback_thread.start()
        self._callback_thread = callback_thread

    def _stop(self):
        log.debug("Waiting for background thread to finish.")
        self._daemon.shutdown()
        self._callback_thread.join()
        self._daemon = None
        self._callback_thread = None
        log.debug("Background thread done.")


def prepare_callback_daemon(extras, protocol, use_direct_calls):
    callback_daemon = None

    if use_direct_calls:
        callback_daemon = DummyHooksCallbackDaemon()
        extras['hooks_module'] = callback_daemon.hooks_module
    else:
        if protocol == 'http':
            callback_daemon = HttpHooksCallbackDaemon()
        else:
            log.error('Unsupported callback daemon protocol "%s"', protocol)
            raise Exception('Unsupported callback daemon protocol.')

        extras['hooks_uri'] = callback_daemon.hooks_uri
        extras['hooks_protocol'] = protocol

    log.debug('Prepared a callback daemon: %s', callback_daemon)
    return callback_daemon, extras


class Hooks(object):
    """
    Exposes the hooks for remote call backs
    """

    def repo_size(self, extras):
        log.debug("Called repo_size of %s object", self)
        return self._call_hook(hooks_base.repo_size, extras)

    def pre_pull(self, extras):
        log.debug("Called pre_pull of %s object", self)
        return self._call_hook(hooks_base.pre_pull, extras)

    def post_pull(self, extras):
        log.debug("Called post_pull of %s object", self)
        return self._call_hook(hooks_base.post_pull, extras)

    def pre_push(self, extras):
        log.debug("Called pre_push of %s object", self)
        return self._call_hook(hooks_base.pre_push, extras)

    def post_push(self, extras):
        log.debug("Called post_push of %s object", self)
        return self._call_hook(hooks_base.post_push, extras)

    def _call_hook(self, hook, extras):
        extras = AttributeDict(extras)
        server_url = extras['server_url']
        request = bootstrap_request(application_url=server_url)

        bootstrap_config(request)  # inject routes and other interfaces

        # inject the user for usage in hooks
        request.user = AttributeDict({'username': extras.username,
                                      'ip_addr': extras.ip,
                                      'user_id': extras.user_id})

        extras.request = request

        try:
            result = hook(extras)
        except Exception as error:
            exc_tb = traceback.format_exc()
            log.exception('Exception when handling hook %s', hook)
            error_args = error.args
            return {
                'status': 128,
                'output': '',
                'exception': type(error).__name__,
                'exception_traceback': exc_tb,
                'exception_args': error_args,
            }
        finally:
            meta.Session.remove()

        log.debug('Got hook call response %s', result)
        return {
            'status': result.status,
            'output': result.output,
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
