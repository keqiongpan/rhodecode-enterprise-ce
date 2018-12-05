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

import os
import sys
import logging
import collections
import tempfile
import time

from paste.gzipper import make_gzip_middleware
import pyramid.events
from pyramid.wsgi import wsgiapp
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.settings import asbool, aslist
from pyramid.httpexceptions import (
    HTTPException, HTTPError, HTTPInternalServerError, HTTPFound, HTTPNotFound)
from pyramid.renderers import render_to_response

from rhodecode.model import meta
from rhodecode.config import patches
from rhodecode.config import utils as config_utils
from rhodecode.config.environment import load_pyramid_environment

import rhodecode.events
from rhodecode.lib.middleware.vcs import VCSMiddleware
from rhodecode.lib.request import Request
from rhodecode.lib.vcs import VCSCommunicationError
from rhodecode.lib.exceptions import VCSServerUnavailable
from rhodecode.lib.middleware.appenlight import wrap_in_appenlight_if_enabled
from rhodecode.lib.middleware.https_fixup import HttpsFixup
from rhodecode.lib.celerylib.loader import configure_celery
from rhodecode.lib.plugins.utils import register_rhodecode_plugin
from rhodecode.lib.utils2 import aslist as rhodecode_aslist, AttributeDict
from rhodecode.lib.exc_tracking import store_exception
from rhodecode.subscribers import (
    scan_repositories_if_enabled, write_js_routes_if_enabled,
    write_metadata_if_needed, inject_app_settings)


log = logging.getLogger(__name__)


def is_http_error(response):
    # error which should have traceback
    return response.status_code > 499


def should_load_all():
    """
    Returns if all application components should be loaded. In some cases it's
    desired to skip apps loading for faster shell script execution
    """
    return True


def make_pyramid_app(global_config, **settings):
    """
    Constructs the WSGI application based on Pyramid.

    Specials:

    * The application can also be integrated like a plugin via the call to
      `includeme`. This is accompanied with the other utility functions which
      are called. Changing this should be done with great care to not break
      cases when these fragments are assembled from another place.

    """

    # Allows to use format style "{ENV_NAME}" placeholders in the configuration. It
    # will be replaced by the value of the environment variable "NAME" in this case.
    start_time = time.time()

    debug = asbool(global_config.get('debug'))
    if debug:
        enable_debug()

    environ = {'ENV_{}'.format(key): value for key, value in os.environ.items()}

    global_config = _substitute_values(global_config, environ)
    settings = _substitute_values(settings, environ)

    sanitize_settings_and_apply_defaults(settings)

    config = Configurator(settings=settings)

    # Apply compatibility patches
    patches.inspect_getargspec()

    load_pyramid_environment(global_config, settings)

    # Static file view comes first
    includeme_first(config)

    includeme(config)

    pyramid_app = config.make_wsgi_app()
    pyramid_app = wrap_app_in_wsgi_middlewares(pyramid_app, config)
    pyramid_app.config = config

    config.configure_celery(global_config['__file__'])
    # creating the app uses a connection - return it after we are done
    meta.Session.remove()
    total_time = time.time() - start_time
    log.info('Pyramid app `%s` created and configured in %.2fs',
             pyramid_app.func_name, total_time)

    return pyramid_app


def not_found_view(request):
    """
    This creates the view which should be registered as not-found-view to
    pyramid.
    """

    if not getattr(request, 'vcs_call', None):
        # handle like regular case with our error_handler
        return error_handler(HTTPNotFound(), request)

    # handle not found view as a vcs call
    settings = request.registry.settings
    ae_client = getattr(request, 'ae_client', None)
    vcs_app = VCSMiddleware(
        HTTPNotFound(), request.registry, settings,
        appenlight_client=ae_client)

    return wsgiapp(vcs_app)(None, request)


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

    if is_http_error(base_response):
        log.exception(
            'error occurred handling this request for path: %s', request.path)

    error_explanation = base_response.explanation or str(base_response)
    if base_response.status_code == 404:
        error_explanation += " Or you don't have permission to access it."
    c = AttributeDict()
    c.error_message = base_response.status
    c.error_explanation = error_explanation
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
    if is_http_error(base_response):
        c.causes.append('Server is overloaded.')
        c.causes.append('Server database connection is lost.')
        c.causes.append('Server expected unhandled error.')

    if hasattr(base_response, 'causes'):
        c.causes = base_response.causes

    c.messages = helpers.flash.pop_messages(request=request)

    exc_info = sys.exc_info()
    c.exception_id = id(exc_info)
    c.show_exception_id = isinstance(base_response, VCSServerUnavailable) \
                          or base_response.status_code > 499
    c.exception_id_url = request.route_url(
        'admin_settings_exception_tracker_show', exception_id=c.exception_id)

    if c.show_exception_id:
        store_exception(c.exception_id, exc_info)

    response = render_to_response(
        '/errors/error_document.mako', {'c': c, 'h': helpers}, request=request,
        response=base_response)

    return response


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


def includeme(config):
    log.debug('Initializing main includeme from %s', os.path.basename(__file__))
    settings = config.registry.settings
    config.set_request_factory(Request)

    # plugin information
    config.registry.rhodecode_plugins = collections.OrderedDict()

    config.add_directive(
        'register_rhodecode_plugin', register_rhodecode_plugin)

    config.add_directive('configure_celery', configure_celery)

    if asbool(settings.get('appenlight', 'false')):
        config.include('appenlight_client.ext.pyramid_tween')

    load_all = should_load_all()

    # Includes which are required. The application would fail without them.
    config.include('pyramid_mako')
    config.include('pyramid_beaker')
    config.include('rhodecode.lib.rc_cache')

    config.include('rhodecode.apps._base.navigation')
    config.include('rhodecode.apps._base.subscribers')
    config.include('rhodecode.tweens')

    config.include('rhodecode.integrations')
    config.include('rhodecode.authentication')

    if load_all:
        from rhodecode.authentication import discover_legacy_plugins
        # load CE authentication plugins
        config.include('rhodecode.authentication.plugins.auth_crowd')
        config.include('rhodecode.authentication.plugins.auth_headers')
        config.include('rhodecode.authentication.plugins.auth_jasig_cas')
        config.include('rhodecode.authentication.plugins.auth_ldap')
        config.include('rhodecode.authentication.plugins.auth_pam')
        config.include('rhodecode.authentication.plugins.auth_rhodecode')
        config.include('rhodecode.authentication.plugins.auth_token')

        # Auto discover authentication plugins and include their configuration.
        discover_legacy_plugins(config)

    # apps
    config.include('rhodecode.apps._base')

    if load_all:
        config.include('rhodecode.apps.ops')
        config.include('rhodecode.apps.admin')
        config.include('rhodecode.apps.channelstream')
        config.include('rhodecode.apps.login')
        config.include('rhodecode.apps.home')
        config.include('rhodecode.apps.journal')
        config.include('rhodecode.apps.repository')
        config.include('rhodecode.apps.repo_group')
        config.include('rhodecode.apps.user_group')
        config.include('rhodecode.apps.search')
        config.include('rhodecode.apps.user_profile')
        config.include('rhodecode.apps.user_group_profile')
        config.include('rhodecode.apps.my_account')
        config.include('rhodecode.apps.svn_support')
        config.include('rhodecode.apps.ssh_support')
        config.include('rhodecode.apps.gist')
        config.include('rhodecode.apps.debug_style')
        config.include('rhodecode.api')

    config.add_route('rhodecode_support', 'https://rhodecode.com/help/', static=True)
    config.add_translation_dirs('rhodecode:i18n/')
    settings['default_locale_name'] = settings.get('lang', 'en')

    # Add subscribers.
    config.add_subscriber(inject_app_settings,
                          pyramid.events.ApplicationCreated)
    config.add_subscriber(scan_repositories_if_enabled,
                          pyramid.events.ApplicationCreated)
    config.add_subscriber(write_metadata_if_needed,
                          pyramid.events.ApplicationCreated)
    config.add_subscriber(write_js_routes_if_enabled,
                          pyramid.events.ApplicationCreated)

    # request custom methods
    config.add_request_method(
        'rhodecode.lib.partial_renderer.get_partial_renderer',
        'get_partial_renderer')

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

    # custom not found view, if our pyramid app doesn't know how to handle
    # the request pass it to potential VCS handling ap
    config.add_notfound_view(not_found_view)
    if not settings.get('debugtoolbar.enabled', False):
        # disabled debugtoolbar handle all exceptions via the error_handlers
        config.add_view(error_handler, context=Exception)

    # all errors including 403/404/50X
    config.add_view(error_handler, context=HTTPError)


def wrap_app_in_wsgi_middlewares(pyramid_app, config):
    """
    Apply outer WSGI middlewares around the application.
    """
    registry = config.registry
    settings = registry.settings

    # enable https redirects based on HTTP_X_URL_SCHEME set by proxy
    pyramid_app = HttpsFixup(pyramid_app, settings)

    pyramid_app, _ae_client = wrap_in_appenlight_if_enabled(
        pyramid_app, settings)
    registry.ae_client = _ae_client

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
            log.debug('Request processing finalized')

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

    settings.setdefault('rhodecode.edition', 'Community Edition')

    if 'mako.default_filters' not in settings:
        # set custom default filters if we don't have it defined
        settings['mako.imports'] = 'from rhodecode.lib.base import h_filter'
        settings['mako.default_filters'] = 'h_filter'

    if 'mako.directories' not in settings:
        mako_directories = settings.setdefault('mako.directories', [
            # Base templates of the original application
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
    _sanitize_cache_settings(settings)

    # configure instance id
    config_utils.set_instance_id(settings)

    return settings


def enable_debug():
    """
    Helper to enable debug on running instance
    :return:
    """
    import tempfile
    import textwrap
    import logging.config

    ini_template = textwrap.dedent("""
    #####################################
    ### DEBUG LOGGING CONFIGURATION  ####
    #####################################
    [loggers]
    keys = root, sqlalchemy, beaker, celery, rhodecode, ssh_wrapper

    [handlers]
    keys = console, console_sql

    [formatters]
    keys = generic, color_formatter, color_formatter_sql

    #############
    ## LOGGERS ##
    #############
    [logger_root]
    level = NOTSET
    handlers = console

    [logger_sqlalchemy]
    level = INFO
    handlers = console_sql
    qualname = sqlalchemy.engine
    propagate = 0

    [logger_beaker]
    level = DEBUG
    handlers =
    qualname = beaker.container
    propagate = 1

    [logger_rhodecode]
    level = DEBUG
    handlers =
    qualname = rhodecode
    propagate = 1

    [logger_ssh_wrapper]
    level = DEBUG
    handlers =
    qualname = ssh_wrapper
    propagate = 1

    [logger_celery]
    level = DEBUG
    handlers =
    qualname = celery


    ##############
    ## HANDLERS ##
    ##############

    [handler_console]
    class = StreamHandler
    args = (sys.stderr, )
    level = DEBUG
    formatter = color_formatter

    [handler_console_sql]
    # "level = DEBUG" logs SQL queries and results.
    # "level = INFO" logs SQL queries.
    # "level = WARN" logs neither.  (Recommended for production systems.)
    class = StreamHandler
    args = (sys.stderr, )
    level = WARN
    formatter = color_formatter_sql

    ################
    ## FORMATTERS ##
    ################

    [formatter_generic]
    class = rhodecode.lib.logging_formatter.ExceptionAwareFormatter
    format = %(asctime)s.%(msecs)03d [%(process)d] %(levelname)-5.5s [%(name)s] %(message)s | %(req_id)s
    datefmt = %Y-%m-%d %H:%M:%S

    [formatter_color_formatter]
    class = rhodecode.lib.logging_formatter.ColorRequestTrackingFormatter
    format = %(asctime)s.%(msecs)03d [%(process)d] %(levelname)-5.5s [%(name)s] %(message)s | %(req_id)s
    datefmt = %Y-%m-%d %H:%M:%S

    [formatter_color_formatter_sql]
    class = rhodecode.lib.logging_formatter.ColorFormatterSql
    format = %(asctime)s.%(msecs)03d [%(process)d] %(levelname)-5.5s [%(name)s] %(message)s
    datefmt = %Y-%m-%d %H:%M:%S    
    """)

    with tempfile.NamedTemporaryFile(prefix='rc_debug_logging_', suffix='.ini',
                                     delete=False) as f:
        log.info('Saved Temporary DEBUG config at %s', f.name)
        f.write(ini_template)

    logging.config.fileConfig(f.name)
    log.debug('DEBUG MODE ON')
    os.remove(f.name)


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
    _string_setting(settings, 'vcs.hooks.host', '127.0.0.1')
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
    # configurations may use 'rhodecode.lib.middleware.utils.scm_app_http', or
    # disabled since 4.13 'vcsserver.scm_app' which is now mapped to 'http'.
    scm_app_impl = settings['vcs.scm_app_implementation']
    if scm_app_impl in ['rhodecode.lib.middleware.utils.scm_app_http', 'vcsserver.scm_app']:
        settings['vcs.scm_app_implementation'] = 'http'


def _sanitize_cache_settings(settings):
    temp_store = tempfile.gettempdir()
    default_cache_dir = os.path.join(temp_store, 'rc_cache')

    # save default, cache dir, and use it for all backends later.
    default_cache_dir = _string_setting(
        settings,
        'cache_dir',
        default_cache_dir, lower=False, default_when_empty=True)

    # ensure we have our dir created
    if not os.path.isdir(default_cache_dir):
        os.makedirs(default_cache_dir, mode=0o755)

    # exception store cache
    _string_setting(
        settings,
        'exception_tracker.store_path',
        temp_store, lower=False, default_when_empty=True)

    # cache_perms
    _string_setting(
        settings,
        'rc_cache.cache_perms.backend',
        'dogpile.cache.rc.file_namespace', lower=False)
    _int_setting(
        settings,
        'rc_cache.cache_perms.expiration_time',
        60)
    _string_setting(
        settings,
        'rc_cache.cache_perms.arguments.filename',
        os.path.join(default_cache_dir, 'rc_cache_1'), lower=False)

    # cache_repo
    _string_setting(
        settings,
        'rc_cache.cache_repo.backend',
        'dogpile.cache.rc.file_namespace', lower=False)
    _int_setting(
        settings,
        'rc_cache.cache_repo.expiration_time',
        60)
    _string_setting(
        settings,
        'rc_cache.cache_repo.arguments.filename',
        os.path.join(default_cache_dir, 'rc_cache_2'), lower=False)

    # cache_license
    _string_setting(
        settings,
        'rc_cache.cache_license.backend',
        'dogpile.cache.rc.file_namespace', lower=False)
    _int_setting(
        settings,
        'rc_cache.cache_license.expiration_time',
        5*60)
    _string_setting(
        settings,
        'rc_cache.cache_license.arguments.filename',
        os.path.join(default_cache_dir, 'rc_cache_3'), lower=False)

    # cache_repo_longterm memory, 96H
    _string_setting(
        settings,
        'rc_cache.cache_repo_longterm.backend',
        'dogpile.cache.rc.memory_lru', lower=False)
    _int_setting(
        settings,
        'rc_cache.cache_repo_longterm.expiration_time',
        345600)
    _int_setting(
        settings,
        'rc_cache.cache_repo_longterm.max_size',
        10000)

    # sql_cache_short
    _string_setting(
        settings,
        'rc_cache.sql_cache_short.backend',
        'dogpile.cache.rc.memory_lru', lower=False)
    _int_setting(
        settings,
        'rc_cache.sql_cache_short.expiration_time',
        30)
    _int_setting(
        settings,
        'rc_cache.sql_cache_short.max_size',
        10000)


def _int_setting(settings, name, default):
    settings[name] = int(settings.get(name, default))
    return settings[name]


def _bool_setting(settings, name, default):
    input_val = settings.get(name, default)
    if isinstance(input_val, unicode):
        input_val = input_val.encode('utf8')
    settings[name] = asbool(input_val)
    return settings[name]


def _list_setting(settings, name, default):
    raw_value = settings.get(name, default)

    old_separator = ','
    if old_separator in raw_value:
        # If we get a comma separated list, pass it to our own function.
        settings[name] = rhodecode_aslist(raw_value, sep=old_separator)
    else:
        # Otherwise we assume it uses pyramids space/newline separation.
        settings[name] = aslist(raw_value)
    return settings[name]


def _string_setting(settings, name, default, lower=True, default_when_empty=False):
    value = settings.get(name, default)

    if default_when_empty and not value:
        # use default value when value is empty
        value = default

    if lower:
        value = value.lower()
    settings[name] = value
    return settings[name]


def _substitute_values(mapping, substitutions):

    try:
        result = {
            # Note: Cannot use regular replacements, since they would clash
            # with the implementation of ConfigParser. Using "format" instead.
            key: value.format(**substitutions)
            for key, value in mapping.items()
        }
    except KeyError as e:
        raise ValueError(
            'Failed to substitute env variable: {}. '
            'Make sure you have specified this env variable without ENV_ prefix'.format(e))
    except ValueError as e:
        log.warning('Failed to substitute ENV variable: %s', e)
        result = mapping

    return result
