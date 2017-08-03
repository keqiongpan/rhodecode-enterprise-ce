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
Pylons middleware initialization
"""
import logging
import traceback
from collections import OrderedDict

from paste.registry import RegistryManager
from paste.gzipper import make_gzip_middleware
from pylons.wsgiapp import PylonsApp
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.settings import asbool, aslist
from pyramid.wsgi import wsgiapp
from pyramid.httpexceptions import (
    HTTPException, HTTPError, HTTPInternalServerError, HTTPFound)
from pyramid.events import ApplicationCreated
from pyramid.renderers import render_to_response
from routes.middleware import RoutesMiddleware
import rhodecode

from rhodecode.model import meta
from rhodecode.config import patches
from rhodecode.config.routing import STATIC_FILE_PREFIX
from rhodecode.config.environment import (
    load_environment, load_pyramid_environment)

from rhodecode.lib.vcs import VCSCommunicationError
from rhodecode.lib.exceptions import VCSServerUnavailable
from rhodecode.lib.middleware.appenlight import wrap_in_appenlight_if_enabled
from rhodecode.lib.middleware.error_handling import (
    PylonsErrorHandlingMiddleware)
from rhodecode.lib.middleware.https_fixup import HttpsFixup
from rhodecode.lib.middleware.vcs import VCSMiddleware
from rhodecode.lib.plugins.utils import register_rhodecode_plugin
from rhodecode.lib.utils2 import aslist as rhodecode_aslist, AttributeDict
from rhodecode.subscribers import (
    scan_repositories_if_enabled, write_js_routes_if_enabled,
    write_metadata_if_needed)


log = logging.getLogger(__name__)


# this is used to avoid avoid the route lookup overhead in routesmiddleware
# for certain routes which won't go to pylons to - eg. static files, debugger
# it is only needed for the pylons migration and can be removed once complete
class SkippableRoutesMiddleware(RoutesMiddleware):
    """ Routes middleware that allows you to skip prefixes """

    def __init__(self, *args, **kw):
        self.skip_prefixes = kw.pop('skip_prefixes', [])
        super(SkippableRoutesMiddleware, self).__init__(*args, **kw)

    def __call__(self, environ, start_response):
        for prefix in self.skip_prefixes:
            if environ['PATH_INFO'].startswith(prefix):
                # added to avoid the case when a missing /_static route falls
                # through to pylons and causes an exception as pylons is
                # expecting wsgiorg.routingargs to be set in the environ
                # by RoutesMiddleware.
                if 'wsgiorg.routing_args' not in environ:
                    environ['wsgiorg.routing_args'] = (None, {})
                return self.app(environ, start_response)

        return super(SkippableRoutesMiddleware, self).__call__(
            environ, start_response)


def make_app(global_conf, static_files=True, **app_conf):
    """Create a Pylons WSGI application and return it

    ``global_conf``
        The inherited configuration for this application. Normally from
        the [DEFAULT] section of the Paste ini file.

    ``app_conf``
        The application's local configuration. Normally specified in
        the [app:<name>] section of the Paste ini file (where <name>
        defaults to main).

    """
    # Apply compatibility patches
    patches.kombu_1_5_1_python_2_7_11()
    patches.inspect_getargspec()

    # Configure the Pylons environment
    config = load_environment(global_conf, app_conf)

    # The Pylons WSGI app
    app = PylonsApp(config=config)

    # Establish the Registry for this application
    app = RegistryManager(app)

    app.config = config

    return app


def make_pyramid_app(global_config, **settings):
    """
    Constructs the WSGI application based on Pyramid and wraps the Pylons based
    application.

    Specials:

    * We migrate from Pylons to Pyramid. While doing this, we keep both
      frameworks functional. This involves moving some WSGI middlewares around
      and providing access to some data internals, so that the old code is
      still functional.

    * The application can also be integrated like a plugin via the call to
      `includeme`. This is accompanied with the other utility functions which
      are called. Changing this should be done with great care to not break
      cases when these fragments are assembled from another place.

    """
    # The edition string should be available in pylons too, so we add it here
    # before copying the settings.
    settings.setdefault('rhodecode.edition', 'Community Edition')

    # As long as our Pylons application does expect "unprepared" settings, make
    # sure that we keep an unmodified copy. This avoids unintentional change of
    # behavior in the old application.
    settings_pylons = settings.copy()

    sanitize_settings_and_apply_defaults(settings)
    config = Configurator(settings=settings)
    add_pylons_compat_data(config.registry, global_config, settings_pylons)

    load_pyramid_environment(global_config, settings)

    includeme_first(config)
    includeme(config)

    pyramid_app = config.make_wsgi_app()
    pyramid_app = wrap_app_in_wsgi_middlewares(pyramid_app, config)
    pyramid_app.config = config

    # creating the app uses a connection - return it after we are done
    meta.Session.remove()

    return pyramid_app


def make_not_found_view(config):
    """
    This creates the view which should be registered as not-found-view to
    pyramid. Basically it contains of the old pylons app, converted to a view.
    Additionally it is wrapped by some other middlewares.
    """
    settings = config.registry.settings
    vcs_server_enabled = settings['vcs.server.enable']

    # Make pylons app from unprepared settings.
    pylons_app = make_app(
        config.registry._pylons_compat_global_config,
        **config.registry._pylons_compat_settings)
    config.registry._pylons_compat_config = pylons_app.config

    # Appenlight monitoring.
    pylons_app, appenlight_client = wrap_in_appenlight_if_enabled(
        pylons_app, settings)

    # The pylons app is executed inside of the pyramid 404 exception handler.
    # Exceptions which are raised inside of it are not handled by pyramid
    # again. Therefore we add a middleware that invokes the error handler in
    # case of an exception or error response. This way we return proper error
    # HTML pages in case of an error.
    reraise = (settings.get('debugtoolbar.enabled', False) or
               rhodecode.disable_error_handler)
    pylons_app = PylonsErrorHandlingMiddleware(
        pylons_app, error_handler, reraise)

    # The VCSMiddleware shall operate like a fallback if pyramid doesn't find a
    # view to handle the request. Therefore it is wrapped around the pylons
    # app. It has to be outside of the error handling otherwise error responses
    # from the vcsserver are converted to HTML error pages. This confuses the
    # command line tools and the user won't get a meaningful error message.
    if vcs_server_enabled:
        pylons_app = VCSMiddleware(
            pylons_app, settings, appenlight_client, registry=config.registry)

    # Convert WSGI app to pyramid view and return it.
    return wsgiapp(pylons_app)


def add_pylons_compat_data(registry, global_config, settings):
    """
    Attach data to the registry to support the Pylons integration.
    """
    registry._pylons_compat_global_config = global_config
    registry._pylons_compat_settings = settings


def error_handler(exception, request):
    import rhodecode
    from rhodecode.lib import helpers

    rhodecode_title = rhodecode.CONFIG.get('rhodecode_title') or 'RhodeCode'

    base_response = HTTPInternalServerError()
    # prefer original exception for the response since it may have headers set
    if isinstance(exception, HTTPException):
        base_response = exception
    elif isinstance(exception, VCSCommunicationError):
        base_response = VCSServerUnavailable()

    def is_http_error(response):
        # error which should have traceback
        return response.status_code > 499

    if is_http_error(base_response):
        log.exception(
            'error occurred handling this request for path: %s', request.path)

    c = AttributeDict()
    c.error_message = base_response.status
    c.error_explanation = base_response.explanation or str(base_response)
    c.visual = AttributeDict()

    c.visual.rhodecode_support_url = (
        request.registry.settings.get('rhodecode_support_url') or
        request.route_url('rhodecode_support')
    )
    c.redirect_time = 0
    c.rhodecode_name = rhodecode_title
    if not c.rhodecode_name:
        c.rhodecode_name = 'Rhodecode'

    c.causes = []
    if hasattr(base_response, 'causes'):
        c.causes = base_response.causes
    c.messages = helpers.flash.pop_messages(request=request)
    c.traceback = traceback.format_exc()
    response = render_to_response(
        '/errors/error_document.mako', {'c': c, 'h': helpers}, request=request,
        response=base_response)

    return response


def includeme(config):
    settings = config.registry.settings

    # plugin information
    config.registry.rhodecode_plugins = OrderedDict()

    config.add_directive(
        'register_rhodecode_plugin', register_rhodecode_plugin)

    if asbool(settings.get('appenlight', 'false')):
        config.include('appenlight_client.ext.pyramid_tween')

    if 'mako.default_filters' not in settings:
        # set custom default filters if we don't have it defined
        settings['mako.imports'] = 'from rhodecode.lib.base import h_filter'
        settings['mako.default_filters'] = 'h_filter'

    # Includes which are required. The application would fail without them.
    config.include('pyramid_mako')
    config.include('pyramid_beaker')

    config.include('rhodecode.authentication')
    config.include('rhodecode.integrations')

    # apps
    config.include('rhodecode.apps._base')
    config.include('rhodecode.apps.ops')

    config.include('rhodecode.apps.admin')
    config.include('rhodecode.apps.channelstream')
    config.include('rhodecode.apps.login')
    config.include('rhodecode.apps.home')
    config.include('rhodecode.apps.journal')
    config.include('rhodecode.apps.repository')
    config.include('rhodecode.apps.repo_group')
    config.include('rhodecode.apps.search')
    config.include('rhodecode.apps.user_profile')
    config.include('rhodecode.apps.my_account')
    config.include('rhodecode.apps.svn_support')
    config.include('rhodecode.apps.ssh_support')
    config.include('rhodecode.apps.gist')

    config.include('rhodecode.apps.debug_style')
    config.include('rhodecode.tweens')
    config.include('rhodecode.api')

    config.add_route(
        'rhodecode_support', 'https://rhodecode.com/help/', static=True)

    config.add_translation_dirs('rhodecode:i18n/')
    settings['default_locale_name'] = settings.get('lang', 'en')

    # Add subscribers.
    config.add_subscriber(scan_repositories_if_enabled, ApplicationCreated)
    config.add_subscriber(write_metadata_if_needed, ApplicationCreated)
    config.add_subscriber(write_js_routes_if_enabled, ApplicationCreated)

    config.add_request_method(
        'rhodecode.lib.partial_renderer.get_partial_renderer',
        'get_partial_renderer')

    # events
    # TODO(marcink): this should be done when pyramid migration is finished
    # config.add_subscriber(
    #     'rhodecode.integrations.integrations_event_handler',
    #     'rhodecode.events.RhodecodeEvent')

    # Set the authorization policy.
    authz_policy = ACLAuthorizationPolicy()
    config.set_authorization_policy(authz_policy)

    # Set the default renderer for HTML templates to mako.
    config.add_mako_renderer('.html')

    config.add_renderer(
        name='json_ext',
        factory='rhodecode.lib.ext_json_renderer.pyramid_ext_json')

    # include RhodeCode plugins
    includes = aslist(settings.get('rhodecode.includes', []))
    for inc in includes:
        config.include(inc)

    # This is the glue which allows us to migrate in chunks. By registering the
    # pylons based application as the "Not Found" view in Pyramid, we will
    # fallback to the old application each time the new one does not yet know
    # how to handle a request.
    config.add_notfound_view(make_not_found_view(config))

    if not settings.get('debugtoolbar.enabled', False):
        # disabled debugtoolbar handle all exceptions via the error_handlers
        config.add_view(error_handler, context=Exception)

    config.add_view(error_handler, context=HTTPError)


def includeme_first(config):
    # redirect automatic browser favicon.ico requests to correct place
    def favicon_redirect(context, request):
        return HTTPFound(
            request.static_path('rhodecode:public/images/favicon.ico'))

    config.add_view(favicon_redirect, route_name='favicon')
    config.add_route('favicon', '/favicon.ico')

    def robots_redirect(context, request):
        return HTTPFound(
            request.static_path('rhodecode:public/robots.txt'))

    config.add_view(robots_redirect, route_name='robots')
    config.add_route('robots', '/robots.txt')

    config.add_static_view(
        '_static/deform', 'deform:static')
    config.add_static_view(
        '_static/rhodecode', path='rhodecode:public', cache_max_age=3600 * 24)


def wrap_app_in_wsgi_middlewares(pyramid_app, config):
    """
    Apply outer WSGI middlewares around the application.

    Part of this has been moved up from the Pylons layer, so that the
    data is also available if old Pylons code is hit through an already ported
    view.
    """
    settings = config.registry.settings

    # enable https redirects based on HTTP_X_URL_SCHEME set by proxy
    pyramid_app = HttpsFixup(pyramid_app, settings)

    # Add RoutesMiddleware to support the pylons compatibility tween during
    # migration to pyramid.

    # TODO(marcink): remove after migration to pyramid
    if hasattr(config.registry, '_pylons_compat_config'):
        routes_map = config.registry._pylons_compat_config['routes.map']
        pyramid_app = SkippableRoutesMiddleware(
            pyramid_app, routes_map,
            skip_prefixes=(STATIC_FILE_PREFIX, '/_debug_toolbar'))

    pyramid_app, _ = wrap_in_appenlight_if_enabled(pyramid_app, settings)

    if settings['gzip_responses']:
        pyramid_app = make_gzip_middleware(
            pyramid_app, settings, compress_level=1)

    # this should be the outer most middleware in the wsgi stack since
    # middleware like Routes make database calls
    def pyramid_app_with_cleanup(environ, start_response):
        try:
            return pyramid_app(environ, start_response)
        finally:
            # Dispose current database session and rollback uncommitted
            # transactions.
            meta.Session.remove()

            # In a single threaded mode server, on non sqlite db we should have
            # '0 Current Checked out connections' at the end of a request,
            # if not, then something, somewhere is leaving a connection open
            pool = meta.Base.metadata.bind.engine.pool
            log.debug('sa pool status: %s', pool.status())

    return pyramid_app_with_cleanup


def sanitize_settings_and_apply_defaults(settings):
    """
    Applies settings defaults and does all type conversion.

    We would move all settings parsing and preparation into this place, so that
    we have only one place left which deals with this part. The remaining parts
    of the application would start to rely fully on well prepared settings.

    This piece would later be split up per topic to avoid a big fat monster
    function.
    """

    # Pyramid's mako renderer has to search in the templates folder so that the
    # old templates still work. Ported and new templates are expected to use
    # real asset specifications for the includes.
    mako_directories = settings.setdefault('mako.directories', [
        # Base templates of the original Pylons application
        'rhodecode:templates',
    ])
    log.debug(
        "Using the following Mako template directories: %s",
        mako_directories)

    # Default includes, possible to change as a user
    pyramid_includes = settings.setdefault('pyramid.includes', [
        'rhodecode.lib.middleware.request_wrapper',
    ])
    log.debug(
        "Using the following pyramid.includes: %s",
        pyramid_includes)

    # TODO: johbo: Re-think this, usually the call to config.include
    # should allow to pass in a prefix.
    settings.setdefault('rhodecode.api.url', '/_admin/api')

    # Sanitize generic settings.
    _list_setting(settings, 'default_encoding', 'UTF-8')
    _bool_setting(settings, 'is_test', 'false')
    _bool_setting(settings, 'gzip_responses', 'false')

    # Call split out functions that sanitize settings for each topic.
    _sanitize_appenlight_settings(settings)
    _sanitize_vcs_settings(settings)

    return settings


def _sanitize_appenlight_settings(settings):
    _bool_setting(settings, 'appenlight', 'false')


def _sanitize_vcs_settings(settings):
    """
    Applies settings defaults and does type conversion for all VCS related
    settings.
    """
    _string_setting(settings, 'vcs.svn.compatible_version', '')
    _string_setting(settings, 'git_rev_filter', '--all')
    _string_setting(settings, 'vcs.hooks.protocol', 'http')
    _string_setting(settings, 'vcs.scm_app_implementation', 'http')
    _string_setting(settings, 'vcs.server', '')
    _string_setting(settings, 'vcs.server.log_level', 'debug')
    _string_setting(settings, 'vcs.server.protocol', 'http')
    _bool_setting(settings, 'startup.import_repos', 'false')
    _bool_setting(settings, 'vcs.hooks.direct_calls', 'false')
    _bool_setting(settings, 'vcs.server.enable', 'true')
    _bool_setting(settings, 'vcs.start_server', 'false')
    _list_setting(settings, 'vcs.backends', 'hg, git, svn')
    _int_setting(settings, 'vcs.connection_timeout', 3600)

    # Support legacy values of vcs.scm_app_implementation. Legacy
    # configurations may use 'rhodecode.lib.middleware.utils.scm_app_http'
    # which is now mapped to 'http'.
    scm_app_impl = settings['vcs.scm_app_implementation']
    if scm_app_impl == 'rhodecode.lib.middleware.utils.scm_app_http':
        settings['vcs.scm_app_implementation'] = 'http'


def _int_setting(settings, name, default):
    settings[name] = int(settings.get(name, default))


def _bool_setting(settings, name, default):
    input = settings.get(name, default)
    if isinstance(input, unicode):
        input = input.encode('utf8')
    settings[name] = asbool(input)


def _list_setting(settings, name, default):
    raw_value = settings.get(name, default)

    old_separator = ','
    if old_separator in raw_value:
        # If we get a comma separated list, pass it to our own function.
        settings[name] = rhodecode_aslist(raw_value, sep=old_separator)
    else:
        # Otherwise we assume it uses pyramids space/newline separation.
        settings[name] = aslist(raw_value)


def _string_setting(settings, name, default, lower=True):
    value = settings.get(name, default)
    if lower:
        value = value.lower()
    settings[name] = value
