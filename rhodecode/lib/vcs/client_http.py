# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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
Client for the VCSServer implemented based on HTTP.
"""

import copy
import logging
import threading
import time
import urllib2
import urlparse
import uuid
import traceback

import pycurl
import msgpack
import requests
from requests.packages.urllib3.util.retry import Retry

import rhodecode
from rhodecode.lib import rc_cache
from rhodecode.lib.rc_cache.utils import compute_key_from_params
from rhodecode.lib.system_info import get_cert_path
from rhodecode.lib.vcs import exceptions, CurlSession

log = logging.getLogger(__name__)


# TODO: mikhail: Keep it in sync with vcsserver's
# HTTPApplication.ALLOWED_EXCEPTIONS
EXCEPTIONS_MAP = {
    'KeyError': KeyError,
    'URLError': urllib2.URLError,
}


def _remote_call(url, payload, exceptions_map, session):
    try:
        response = session.post(url, data=msgpack.packb(payload))
    except pycurl.error as e:
        msg = '{}. \npycurl traceback: {}'.format(e, traceback.format_exc())
        raise exceptions.HttpVCSCommunicationError(msg)
    except Exception as e:
        message = getattr(e, 'message', '')
        if 'Failed to connect' in message:
            # gevent doesn't return proper pycurl errors
            raise exceptions.HttpVCSCommunicationError(e)
        else:
            raise

    if response.status_code >= 400:
        log.error('Call to %s returned non 200 HTTP code: %s',
                  url, response.status_code)
        raise exceptions.HttpVCSCommunicationError(repr(response.content))

    try:
        response = msgpack.unpackb(response.content)
    except Exception:
        log.exception('Failed to decode response %r', response.content)
        raise

    error = response.get('error')
    if error:
        type_ = error.get('type', 'Exception')
        exc = exceptions_map.get(type_, Exception)
        exc = exc(error.get('message'))
        try:
            exc._vcs_kind = error['_vcs_kind']
        except KeyError:
            pass

        try:
            exc._vcs_server_traceback = error['traceback']
            exc._vcs_server_org_exc_name = error['org_exc']
            exc._vcs_server_org_exc_tb = error['org_exc_tb']
        except KeyError:
            pass

        raise exc
    return response.get('result')


def _streaming_remote_call(url, payload, exceptions_map, session, chunk_size):
    try:
        response = session.post(url, data=msgpack.packb(payload))
    except pycurl.error as e:
        msg = '{}. \npycurl traceback: {}'.format(e, traceback.format_exc())
        raise exceptions.HttpVCSCommunicationError(msg)
    except Exception as e:
        message = getattr(e, 'message', '')
        if 'Failed to connect' in message:
            # gevent doesn't return proper pycurl errors
            raise exceptions.HttpVCSCommunicationError(e)
        else:
            raise

    if response.status_code >= 400:
        log.error('Call to %s returned non 200 HTTP code: %s',
                  url, response.status_code)
        raise exceptions.HttpVCSCommunicationError(repr(response.content))

    return response.iter_content(chunk_size=chunk_size)


class ServiceConnection(object):
    def __init__(self, server_and_port, backend_endpoint, session_factory):
        self.url = urlparse.urljoin('http://%s' % server_and_port, backend_endpoint)
        self._session_factory = session_factory

    def __getattr__(self, name):
        def f(*args, **kwargs):
            return self._call(name, *args, **kwargs)
        return f

    @exceptions.map_vcs_exceptions
    def _call(self, name, *args, **kwargs):
        payload = {
            'id': str(uuid.uuid4()),
            'method': name,
            'params': {'args': args, 'kwargs': kwargs}
        }
        return _remote_call(
            self.url, payload, EXCEPTIONS_MAP, self._session_factory())


class RemoteVCSMaker(object):

    def __init__(self, server_and_port, backend_endpoint, backend_type, session_factory):
        self.url = urlparse.urljoin('http://%s' % server_and_port, backend_endpoint)
        self.stream_url = urlparse.urljoin('http://%s' % server_and_port, backend_endpoint+'/stream')

        self._session_factory = session_factory
        self.backend_type = backend_type

    @classmethod
    def init_cache_region(cls, repo_id):
        cache_namespace_uid = 'cache_repo.{}'.format(repo_id)
        region = rc_cache.get_or_create_region('cache_repo', cache_namespace_uid)
        return region, cache_namespace_uid

    def __call__(self, path, repo_id, config, with_wire=None):
        log.debug('%s RepoMaker call on %s', self.backend_type.upper(), path)
        return RemoteRepo(path, repo_id, config, self, with_wire=with_wire)

    def __getattr__(self, name):
        def remote_attr(*args, **kwargs):
            return self._call(name, *args, **kwargs)
        return remote_attr

    @exceptions.map_vcs_exceptions
    def _call(self, func_name, *args, **kwargs):
        payload = {
            'id': str(uuid.uuid4()),
            'method': func_name,
            'backend': self.backend_type,
            'params': {'args': args, 'kwargs': kwargs}
        }
        url = self.url
        return _remote_call(url, payload, EXCEPTIONS_MAP, self._session_factory())


class RemoteRepo(object):
    CHUNK_SIZE = 16384

    def __init__(self, path, repo_id, config, remote_maker, with_wire=None):
        self.url = remote_maker.url
        self.stream_url = remote_maker.stream_url
        self._session = remote_maker._session_factory()
        self._cache_region, self._cache_namespace = \
            remote_maker.init_cache_region(repo_id)

        with_wire = with_wire or {}

        repo_state_uid = with_wire.get('repo_state_uid') or 'state'
        self._wire = {
            "path": path,  # repo path
            "repo_id": repo_id,
            "config": config,
            "repo_state_uid": repo_state_uid,
            "context": self._create_vcs_cache_context(path, repo_state_uid)
        }

        if with_wire:
            self._wire.update(with_wire)

        # NOTE(johbo): Trading complexity for performance. Avoiding the call to
        # log.debug brings a few percent gain even if is is not active.
        if log.isEnabledFor(logging.DEBUG):
            self._call_with_logging = True

        self.cert_dir = get_cert_path(rhodecode.CONFIG.get('__file__'))

    def __getattr__(self, name):

        if name.startswith('stream:'):
            def repo_remote_attr(*args, **kwargs):
                return self._call_stream(name, *args, **kwargs)
        else:
            def repo_remote_attr(*args, **kwargs):
                return self._call(name, *args, **kwargs)

        return repo_remote_attr

    def _base_call(self, name, *args, **kwargs):
        # TODO: oliver: This is currently necessary pre-call since the
        # config object is being changed for hooking scenarios
        wire = copy.deepcopy(self._wire)
        wire["config"] = wire["config"].serialize()
        wire["config"].append(('vcs', 'ssl_dir', self.cert_dir))

        payload = {
            'id': str(uuid.uuid4()),
            'method': name,
            'params': {'wire': wire, 'args': args, 'kwargs': kwargs}
        }

        context_uid = wire.get('context')
        return context_uid, payload

    @exceptions.map_vcs_exceptions
    def _call(self, name, *args, **kwargs):
        context_uid, payload = self._base_call(name, *args, **kwargs)
        url = self.url

        start = time.time()

        cache_on = False
        cache_key = ''
        local_cache_on = rhodecode.CONFIG.get('vcs.methods.cache')

        cache_methods = [
            'branches', 'tags', 'bookmarks',
            'is_large_file', 'is_binary', 'fctx_size', 'node_history', 'blob_raw_length',
            'revision', 'tree_items',
            'ctx_list',
            'bulk_request',
        ]

        if local_cache_on and name in cache_methods:
            cache_on = True
            repo_state_uid = self._wire['repo_state_uid']
            call_args = [a for a in args]
            cache_key = compute_key_from_params(repo_state_uid, name, *call_args)

        @self._cache_region.conditional_cache_on_arguments(
            namespace=self._cache_namespace, condition=cache_on and cache_key)
        def remote_call(_cache_key):
            if self._call_with_logging:
                log.debug('Calling %s@%s with args:%.10240r. wire_context: %s cache_on: %s',
                          url, name, args, context_uid, cache_on)
            return _remote_call(url, payload, EXCEPTIONS_MAP, self._session)

        result = remote_call(cache_key)
        if self._call_with_logging:
            log.debug('Call %s@%s took: %.4fs. wire_context: %s',
                      url, name, time.time()-start, context_uid)
        return result

    @exceptions.map_vcs_exceptions
    def _call_stream(self, name, *args, **kwargs):
        context_uid, payload = self._base_call(name, *args, **kwargs)
        payload['chunk_size'] = self.CHUNK_SIZE
        url = self.stream_url

        start = time.time()
        if self._call_with_logging:
            log.debug('Calling %s@%s with args:%.10240r. wire_context: %s',
                      url, name, args, context_uid)

        result = _streaming_remote_call(url, payload, EXCEPTIONS_MAP, self._session,
                                        self.CHUNK_SIZE)

        if self._call_with_logging:
            log.debug('Call %s@%s took: %.4fs. wire_context: %s',
                      url, name, time.time()-start, context_uid)
        return result

    def __getitem__(self, key):
        return self.revision(key)

    def _create_vcs_cache_context(self, *args):
        """
        Creates a unique string which is passed to the VCSServer on every
        remote call. It is used as cache key in the VCSServer.
        """
        hash_key = '-'.join(map(str, args))
        return str(uuid.uuid5(uuid.NAMESPACE_URL, hash_key))

    def invalidate_vcs_cache(self):
        """
        This invalidates the context which is sent to the VCSServer on every
        call to a remote method. It forces the VCSServer to create a fresh
        repository instance on the next call to a remote method.
        """
        self._wire['context'] = str(uuid.uuid4())


class VcsHttpProxy(object):

    CHUNK_SIZE = 16384

    def __init__(self, server_and_port, backend_endpoint):
        retries = Retry(total=5, connect=None, read=None, redirect=None)

        adapter = requests.adapters.HTTPAdapter(max_retries=retries)
        self.base_url = urlparse.urljoin('http://%s' % server_and_port, backend_endpoint)
        self.session = requests.Session()
        self.session.mount('http://', adapter)

    def handle(self, environment, input_data, *args, **kwargs):
        data = {
            'environment': environment,
            'input_data': input_data,
            'args': args,
            'kwargs': kwargs
        }
        result = self.session.post(
            self.base_url, msgpack.packb(data), stream=True)
        return self._get_result(result)

    def _deserialize_and_raise(self, error):
        exception = Exception(error['message'])
        try:
            exception._vcs_kind = error['_vcs_kind']
        except KeyError:
            pass
        raise exception

    def _iterate(self, result):
        unpacker = msgpack.Unpacker()
        for line in result.iter_content(chunk_size=self.CHUNK_SIZE):
            unpacker.feed(line)
            for chunk in unpacker:
                yield chunk

    def _get_result(self, result):
        iterator = self._iterate(result)
        error = iterator.next()
        if error:
            self._deserialize_and_raise(error)

        status = iterator.next()
        headers = iterator.next()

        return iterator, status, headers


class ThreadlocalSessionFactory(object):
    """
    Creates one CurlSession per thread on demand.
    """

    def __init__(self):
        self._thread_local = threading.local()

    def __call__(self):
        if not hasattr(self._thread_local, 'curl_session'):
            self._thread_local.curl_session = CurlSession()
        return self._thread_local.curl_session
