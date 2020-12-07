# Copyright (c) 2010 Agendaless Consulting and Contributors.
# (http://www.agendaless.com), All Rights Reserved
# License: BSD-derived (http://www.repoze.org/LICENSE.txt)
# With Patches from RhodeCode GmBH


import os

from beaker import cache
from beaker.session import SessionObject
from beaker.util import coerce_cache_params
from beaker.util import coerce_session_params

from pyramid.interfaces import ISession
from pyramid.settings import asbool
from zope.interface import implementer

from binascii import hexlify


def BeakerSessionFactoryConfig(**options):
    """ Return a Pyramid session factory using Beaker session settings
    supplied directly as ``**options``"""

    class PyramidBeakerSessionObject(SessionObject):
        _options = options
        _cookie_on_exception = _options.pop('cookie_on_exception', True)
        _constant_csrf_token = _options.pop('constant_csrf_token', False)

        def __init__(self, request):
            SessionObject.__init__(self, request.environ, **self._options)

            def session_callback(request, response):
                exception = getattr(request, 'exception', None)
                file_response = getattr(request, '_file_response', None)

                if file_response is None \
                        and (exception is None or self._cookie_on_exception) \
                        and self.accessed():
                    self.persist()
                    headers = self.__dict__['_headers']
                    if headers.get('set_cookie') and headers.get('cookie_out'):
                        response.headerlist.append(('Set-Cookie', headers['cookie_out']))
            request.add_response_callback(session_callback)

        # ISession API

        @property
        def id(self):
            # this is as inspected in SessionObject.__init__
            if self.__dict__['_params'].get('type') != 'cookie':
                return self._session().id
            return None

        @property
        def new(self):
            return self.last_accessed is None

        changed = SessionObject.save

        # modifying dictionary methods

        @call_save
        def clear(self):
            return self._session().clear()

        @call_save
        def update(self, d, **kw):
            return self._session().update(d, **kw)

        @call_save
        def setdefault(self, k, d=None):
            return self._session().setdefault(k, d)

        @call_save
        def pop(self, k, d=None):
            return self._session().pop(k, d)

        @call_save
        def popitem(self):
            return self._session().popitem()

        __setitem__ = call_save(SessionObject.__setitem__)
        __delitem__ = call_save(SessionObject.__delitem__)

        # Flash API methods
        def flash(self, msg, queue='', allow_duplicate=True):
            storage = self.setdefault('_f_' + queue, [])
            if allow_duplicate or (msg not in storage):
                storage.append(msg)

        def pop_flash(self, queue=''):
            storage = self.pop('_f_' + queue, [])
            return storage

        def peek_flash(self, queue=''):
            storage = self.get('_f_' + queue, [])
            return storage

        # CSRF API methods
        def new_csrf_token(self):
            token = (self._constant_csrf_token
                     or hexlify(os.urandom(20)).decode('ascii'))
            self['_csrft_'] = token
            return token

        def get_csrf_token(self):
            token = self.get('_csrft_', None)
            if token is None:
                token = self.new_csrf_token()
            return token

    return implementer(ISession)(PyramidBeakerSessionObject)


def call_save(wrapped):
    """ By default, in non-auto-mode beaker badly wants people to
    call save even though it should know something has changed when
    a mutating method is called.  This hack should be removed if
    Beaker ever starts to do this by default. """
    def save(session, *arg, **kw):
        value = wrapped(session, *arg, **kw)
        session.save()
        return value
    save.__doc__ = wrapped.__doc__
    return save


def session_factory_from_settings(settings):
    """ Return a Pyramid session factory using Beaker session settings
    supplied from a Paste configuration file"""
    prefixes = ('session.', 'beaker.session.')
    options = {}

    # Pull out any config args meant for beaker session. if there are any
    for k, v in settings.items():
        for prefix in prefixes:
            if k.startswith(prefix):
                option_name = k[len(prefix):]
                if option_name == 'cookie_on_exception':
                    v = asbool(v)
                options[option_name] = v

    options = coerce_session_params(options)
    return BeakerSessionFactoryConfig(**options)


def includeme(config):
    session_factory = session_factory_from_settings(config.registry.settings)
    config.set_session_factory(session_factory)
