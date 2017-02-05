# -*- coding: utf-8 -*-

# Copyright (C) 2014-2017 RhodeCode GmbH
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
Provides the implementation of various client utilities to reach the vcsserver.
"""


import copy
import logging
import uuid
import weakref

import Pyro4
from pyramid.threadlocal import get_current_request
from Pyro4.errors import CommunicationError, ConnectionClosedError, DaemonError

from rhodecode.lib.vcs import exceptions
from rhodecode.lib.vcs.conf import settings

log = logging.getLogger(__name__)


class RepoMaker(object):

    def __init__(self, proxy_factory):
        self._proxy_factory = proxy_factory

    def __call__(self, path, config, with_wire=None):
        log.debug('RepoMaker call on %s', path)
        return RemoteRepo(
            path, config, remote_proxy=self._proxy_factory(),
            with_wire=with_wire)

    def __getattr__(self, name):
        remote_proxy = self._proxy_factory()
        func = _get_proxy_method(remote_proxy, name)
        return _wrap_remote_call(remote_proxy, func)


class RequestScopeProxyFactory(object):
    """
    This factory returns pyro proxy instances based on a per request scope.
    It returns the same instance if called from within the same request and
    different instances if called from different requests.
    """

    def __init__(self, remote_uri):
        self._remote_uri = remote_uri
        self._proxy_pool = []
        self._borrowed_proxies = {}

    def __call__(self, request=None):
        """
        Wrapper around `getProxy`.
        """
        request = request or get_current_request()
        return self.getProxy(request)

    def getProxy(self, request):
        """
        Call this to get the pyro proxy instance for the request.
        """

        # If called without a request context we return new proxy instances
        # on every call. This allows to run e.g. invoke tasks.
        if request is None:
            log.info('Creating pyro proxy without request context for '
                     'remote_uri=%s', self._remote_uri)
            return Pyro4.Proxy(self._remote_uri)

        # If there is an already borrowed proxy for the request context we
        # return that instance instead of creating a new one.
        if request in self._borrowed_proxies:
            return self._borrowed_proxies[request]

        # Get proxy from pool or create new instance.
        try:
            proxy = self._proxy_pool.pop()
        except IndexError:
            log.info('Creating pyro proxy for remote_uri=%s', self._remote_uri)
            proxy = Pyro4.Proxy(self._remote_uri)

        # Mark proxy as borrowed for the request context and add a callback
        # that returns it when the request processing is finished.
        self._borrowed_proxies[request] = proxy
        request.add_finished_callback(self._returnProxy)

        return proxy

    def _returnProxy(self, request):
        """
        Callback that gets called by pyramid when the request is finished.
        It puts the proxy back into the pool.
        """
        if request in self._borrowed_proxies:
            proxy = self._borrowed_proxies.pop(request)
            self._proxy_pool.append(proxy)
        else:
            log.warn('Return proxy for remote_uri=%s but no proxy borrowed '
                     'for this request.', self._remote_uri)


class RemoteRepo(object):

    def __init__(self, path, config, remote_proxy, with_wire=None):
        self._wire = {
            "path": path,
            "config": config,
            "context": self._create_vcs_cache_context(),
        }
        if with_wire:
            self._wire.update(with_wire)
        self._remote_proxy = remote_proxy
        self.refs = RefsWrapper(self)

    def __getattr__(self, name):
        log.debug('Calling %s@%s', self._remote_proxy, name)
        # TODO: oliver: This is currently necessary pre-call since the
        # config object is being changed for hooking scenarios
        wire = copy.deepcopy(self._wire)
        wire["config"] = wire["config"].serialize()

        try:
            func = _get_proxy_method(self._remote_proxy, name)
        except DaemonError as e:
            if e.message == 'unknown object':
                raise exceptions.VCSBackendNotSupportedError
            else:
                raise

        return _wrap_remote_call(self._remote_proxy, func, wire)

    def __getitem__(self, key):
        return self.revision(key)

    def _create_vcs_cache_context(self):
        """
        Creates a unique string which is passed to the VCSServer on every
        remote call. It is used as cache key in the VCSServer.
        """
        return str(uuid.uuid4())

    def invalidate_vcs_cache(self):
        """
        This is a no-op method for the pyro4 backend but we want to have the
        same API for client.RemoteRepo and client_http.RemoteRepo classes.
        """


def _get_proxy_method(proxy, name):
    try:
        return getattr(proxy, name)
    except CommunicationError:
        raise exceptions.PyroVCSCommunicationError(
            'Unable to connect to remote pyro server %s' % proxy)


def _wrap_remote_call(proxy, func, *args):
    all_args = list(args)

    @exceptions.map_vcs_exceptions
    def caller(*args, **kwargs):
        all_args.extend(args)
        try:
            return func(*all_args, **kwargs)
        except ConnectionClosedError:
            log.debug('Connection to VCSServer closed, trying to reconnect.')
            proxy._pyroReconnect(tries=settings.PYRO_RECONNECT_TRIES)

            return func(*all_args, **kwargs)

    return caller


class RefsWrapper(object):

    def __init__(self, repo):
        self._repo = weakref.proxy(repo)

    def __setitem__(self, key, value):
        self._repo._assign_ref(key, value)


class FunctionWrapper(object):

    def __init__(self, func, wire):
        self._func = func
        self._wire = wire

    @exceptions.map_vcs_exceptions
    def __call__(self, *args, **kwargs):
        return self._func(self._wire, *args, **kwargs)
