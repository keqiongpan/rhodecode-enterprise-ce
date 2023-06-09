# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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
The base Controller API
Provides the BaseController class for subclassing. And usage in different
controllers
"""

import logging
import socket

import markupsafe
import ipaddress

from paste.auth.basic import AuthBasicAuthenticator
from paste.httpexceptions import HTTPUnauthorized, HTTPForbidden, get_exception
from paste.httpheaders import WWW_AUTHENTICATE, AUTHORIZATION

import rhodecode
from rhodecode.apps._base import TemplateArgs
from rhodecode.authentication.base import VCS_TYPE
from rhodecode.lib import auth, utils2
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import AuthUser, CookieStoreWrapper
from rhodecode.lib.exceptions import UserCreationError
from rhodecode.lib.utils import (password_changed, get_enabled_hook_classes)
from rhodecode.lib.utils2 import (
    str2bool, safe_unicode, AttributeDict, safe_int, sha1, aslist, safe_str)
from rhodecode.model.db import Repository, User, ChangesetComment, UserBookmark
from rhodecode.model.notification import NotificationModel
from rhodecode.model.settings import VcsSettingsModel, SettingsModel

log = logging.getLogger(__name__)


def _filter_proxy(ip):
    """
    Passed in IP addresses in HEADERS can be in a special format of multiple
    ips. Those comma separated IPs are passed from various proxies in the
    chain of request processing. The left-most being the original client.
    We only care about the first IP which came from the org. client.

    :param ip: ip string from headers
    """
    if ',' in ip:
        _ips = ip.split(',')
        _first_ip = _ips[0].strip()
        log.debug('Got multiple IPs %s, using %s', ','.join(_ips), _first_ip)
        return _first_ip
    return ip


def _filter_port(ip):
    """
    Removes a port from ip, there are 4 main cases to handle here.
    - ipv4 eg. 127.0.0.1
    - ipv6 eg. ::1
    - ipv4+port eg. 127.0.0.1:8080
    - ipv6+port eg. [::1]:8080

    :param ip:
    """
    def is_ipv6(ip_addr):
        if hasattr(socket, 'inet_pton'):
            try:
                socket.inet_pton(socket.AF_INET6, ip_addr)
            except socket.error:
                return False
        else:
            # fallback to ipaddress
            try:
                ipaddress.IPv6Address(safe_unicode(ip_addr))
            except Exception:
                return False
        return True

    if ':' not in ip:  # must be ipv4 pure ip
        return ip

    if '[' in ip and ']' in ip:  # ipv6 with port
        return ip.split(']')[0][1:].lower()

    # must be ipv6 or ipv4 with port
    if is_ipv6(ip):
        return ip
    else:
        ip, _port = ip.split(':')[:2]  # means ipv4+port
        return ip


def get_ip_addr(environ):
    proxy_key = 'HTTP_X_REAL_IP'
    proxy_key2 = 'HTTP_X_FORWARDED_FOR'
    def_key = 'REMOTE_ADDR'
    _filters = lambda x: _filter_port(_filter_proxy(x))

    ip = environ.get(proxy_key)
    if ip:
        return _filters(ip)

    ip = environ.get(proxy_key2)
    if ip:
        return _filters(ip)

    ip = environ.get(def_key, '0.0.0.0')
    return _filters(ip)


def get_server_ip_addr(environ, log_errors=True):
    hostname = environ.get('SERVER_NAME')
    try:
        return socket.gethostbyname(hostname)
    except Exception as e:
        if log_errors:
            # in some cases this lookup is not possible, and we don't want to
            # make it an exception in logs
            log.exception('Could not retrieve server ip address: %s', e)
        return hostname


def get_server_port(environ):
    return environ.get('SERVER_PORT')


def get_access_path(environ):
    path = environ.get('PATH_INFO')
    org_req = environ.get('pylons.original_request')
    if org_req:
        path = org_req.environ.get('PATH_INFO')
    return path


def get_user_agent(environ):
    return environ.get('HTTP_USER_AGENT')


def vcs_operation_context(
        environ, repo_name, username, action, scm, check_locking=True,
        is_shadow_repo=False, check_branch_perms=False, detect_force_push=False):
    """
    Generate the context for a vcs operation, e.g. push or pull.

    This context is passed over the layers so that hooks triggered by the
    vcs operation know details like the user, the user's IP address etc.

    :param check_locking: Allows to switch of the computation of the locking
        data. This serves mainly the need of the simplevcs middleware to be
        able to disable this for certain operations.

    """
    # Tri-state value: False: unlock, None: nothing, True: lock
    make_lock = None
    locked_by = [None, None, None]
    is_anonymous = username == User.DEFAULT_USER
    user = User.get_by_username(username)
    if not is_anonymous and check_locking:
        log.debug('Checking locking on repository "%s"', repo_name)
        repo = Repository.get_by_repo_name(repo_name)
        make_lock, __, locked_by = repo.get_locking_state(
            action, user.user_id)
    user_id = user.user_id
    settings_model = VcsSettingsModel(repo=repo_name)
    ui_settings = settings_model.get_ui_settings()

    # NOTE(marcink): This should be also in sync with
    # rhodecode/apps/ssh_support/lib/backends/base.py:update_environment scm_data
    store = [x for x in ui_settings if x.key == '/']
    repo_store = ''
    if store:
        repo_store = store[0].value

    scm_data = {
        'ip': get_ip_addr(environ),
        'username': username,
        'user_id': user_id,
        'action': action,
        'repository': repo_name,
        'scm': scm,
        'config': rhodecode.CONFIG['__file__'],
        'repo_store': repo_store,
        'make_lock': make_lock,
        'locked_by': locked_by,
        'server_url': utils2.get_server_url(environ),
        'user_agent': get_user_agent(environ),
        'hooks': get_enabled_hook_classes(ui_settings),
        'is_shadow_repo': is_shadow_repo,
        'detect_force_push': detect_force_push,
        'check_branch_perms': check_branch_perms,
    }
    return scm_data


class BasicAuth(AuthBasicAuthenticator):

    def __init__(self, realm, authfunc, registry, auth_http_code=None,
                 initial_call_detection=False, acl_repo_name=None, rc_realm=''):
        self.realm = realm
        self.rc_realm = rc_realm
        self.initial_call = initial_call_detection
        self.authfunc = authfunc
        self.registry = registry
        self.acl_repo_name = acl_repo_name
        self._rc_auth_http_code = auth_http_code

    def _get_response_from_code(self, http_code):
        try:
            return get_exception(safe_int(http_code))
        except Exception:
            log.exception('Failed to fetch response for code %s', http_code)
            return HTTPForbidden

    def get_rc_realm(self):
        return safe_str(self.rc_realm)

    def build_authentication(self):
        head = WWW_AUTHENTICATE.tuples('Basic realm="%s"' % self.realm)
        if self._rc_auth_http_code and not self.initial_call:
            # return alternative HTTP code if alternative http return code
            # is specified in RhodeCode config, but ONLY if it's not the
            # FIRST call
            custom_response_klass = self._get_response_from_code(
                self._rc_auth_http_code)
            return custom_response_klass(headers=head)
        return HTTPUnauthorized(headers=head)

    def authenticate(self, environ):
        authorization = AUTHORIZATION(environ)
        if not authorization:
            return self.build_authentication()
        (authmeth, auth) = authorization.split(' ', 1)
        if 'basic' != authmeth.lower():
            return self.build_authentication()
        auth = auth.strip().decode('base64')
        _parts = auth.split(':', 1)
        if len(_parts) == 2:
            username, password = _parts
            auth_data = self.authfunc(
                    username, password, environ, VCS_TYPE,
                    registry=self.registry, acl_repo_name=self.acl_repo_name)
            if auth_data:
                return {'username': username, 'auth_data': auth_data}
            if username and password:
                # we mark that we actually executed authentication once, at
                # that point we can use the alternative auth code
                self.initial_call = False

        return self.build_authentication()

    __call__ = authenticate


def calculate_version_hash(config):
    return sha1(
        config.get('beaker.session.secret', '') +
        rhodecode.__version__)[:8]


def get_current_lang(request):
    # NOTE(marcink): remove after pyramid move
    try:
        return translation.get_lang()[0]
    except:
        pass

    return getattr(request, '_LOCALE_', request.locale_name)


def attach_context_attributes(context, request, user_id=None, is_api=None):
    """
    Attach variables into template context called `c`.
    """
    config = request.registry.settings

    rc_config = SettingsModel().get_all_settings(cache=True, from_request=False)
    context.rc_config = rc_config
    context.rhodecode_version = rhodecode.__version__
    context.rhodecode_edition = config.get('rhodecode.edition')
    context.rhodecode_edition_id = config.get('rhodecode.edition_id')
    # unique secret + version does not leak the version but keep consistency
    context.rhodecode_version_hash = calculate_version_hash(config)

    # Default language set for the incoming request
    context.language = get_current_lang(request)

    # Visual options
    context.visual = AttributeDict({})

    # DB stored Visual Items
    context.visual.show_public_icon = str2bool(
        rc_config.get('rhodecode_show_public_icon'))
    context.visual.show_private_icon = str2bool(
        rc_config.get('rhodecode_show_private_icon'))
    context.visual.stylify_metatags = str2bool(
        rc_config.get('rhodecode_stylify_metatags'))
    context.visual.dashboard_items = safe_int(
        rc_config.get('rhodecode_dashboard_items', 100))
    context.visual.admin_grid_items = safe_int(
        rc_config.get('rhodecode_admin_grid_items', 100))
    context.visual.show_revision_number = str2bool(
        rc_config.get('rhodecode_show_revision_number', True))
    context.visual.show_sha_length = safe_int(
        rc_config.get('rhodecode_show_sha_length', 100))
    context.visual.repository_fields = str2bool(
        rc_config.get('rhodecode_repository_fields'))
    context.visual.show_version = str2bool(
        rc_config.get('rhodecode_show_version'))
    context.visual.use_gravatar = str2bool(
        rc_config.get('rhodecode_use_gravatar'))
    context.visual.gravatar_url = rc_config.get('rhodecode_gravatar_url')
    context.visual.default_renderer = rc_config.get(
        'rhodecode_markup_renderer', 'rst')
    context.visual.comment_types = ChangesetComment.COMMENT_TYPES
    context.visual.rhodecode_support_url = \
        rc_config.get('rhodecode_support_url') or h.route_url('rhodecode_support')

    context.visual.affected_files_cut_off = 60

    context.pre_code = rc_config.get('rhodecode_pre_code')
    context.post_code = rc_config.get('rhodecode_post_code')
    context.rhodecode_name = rc_config.get('rhodecode_title')
    context.default_encodings = aslist(config.get('default_encoding'), sep=',')
    # if we have specified default_encoding in the request, it has more
    # priority
    if request.GET.get('default_encoding'):
        context.default_encodings.insert(0, request.GET.get('default_encoding'))
    context.clone_uri_tmpl = rc_config.get('rhodecode_clone_uri_tmpl')
    context.clone_uri_id_tmpl = rc_config.get('rhodecode_clone_uri_id_tmpl')
    context.clone_uri_ssh_tmpl = rc_config.get('rhodecode_clone_uri_ssh_tmpl')

    # INI stored
    context.labs_active = str2bool(
        config.get('labs_settings_active', 'false'))
    context.ssh_enabled = str2bool(
        config.get('ssh.generate_authorized_keyfile', 'false'))
    context.ssh_key_generator_enabled = str2bool(
        config.get('ssh.enable_ui_key_generator', 'true'))

    context.visual.allow_repo_location_change = str2bool(
        config.get('allow_repo_location_change', True))
    context.visual.allow_custom_hooks_settings = str2bool(
        config.get('allow_custom_hooks_settings', True))
    context.debug_style = str2bool(config.get('debug_style', False))

    context.rhodecode_instanceid = config.get('instance_id')

    context.visual.cut_off_limit_diff = safe_int(
        config.get('cut_off_limit_diff'))
    context.visual.cut_off_limit_file = safe_int(
        config.get('cut_off_limit_file'))

    context.license = AttributeDict({})
    context.license.hide_license_info = str2bool(
        config.get('license.hide_license_info', False))

    # AppEnlight
    context.appenlight_enabled = str2bool(config.get('appenlight', 'false'))
    context.appenlight_api_public_key = config.get(
        'appenlight.api_public_key', '')
    context.appenlight_server_url = config.get('appenlight.server_url', '')

    diffmode = {
        "unified": "unified",
        "sideside": "sideside"
    }.get(request.GET.get('diffmode'))

    if is_api is not None:
        is_api = hasattr(request, 'rpc_user')
    session_attrs = {
        # defaults
        "clone_url_format": "http",
        "diffmode": "sideside",
        "license_fingerprint": request.session.get('license_fingerprint')
    }

    if not is_api:
        # don't access pyramid session for API calls
        if diffmode and diffmode != request.session.get('rc_user_session_attr.diffmode'):
            request.session['rc_user_session_attr.diffmode'] = diffmode

        # session settings per user

        for k, v in request.session.items():
            pref = 'rc_user_session_attr.'
            if k and k.startswith(pref):
                k = k[len(pref):]
                session_attrs[k] = v

    context.user_session_attrs = session_attrs

    # JS template context
    context.template_context = {
        'repo_name': None,
        'repo_type': None,
        'repo_landing_commit': None,
        'rhodecode_user': {
            'username': None,
            'email': None,
            'notification_status': False
        },
        'session_attrs': session_attrs,
        'visual': {
            'default_renderer': None
        },
        'commit_data': {
            'commit_id': None
        },
        'pull_request_data': {'pull_request_id': None},
        'timeago': {
            'refresh_time': 120 * 1000,
            'cutoff_limit': 1000 * 60 * 60 * 24 * 7
        },
        'pyramid_dispatch': {

        },
        'extra': {'plugins': {}}
    }
    # END CONFIG VARS
    if is_api:
        csrf_token = None
    else:
        csrf_token = auth.get_csrf_token(session=request.session)

    context.csrf_token = csrf_token
    context.backends = rhodecode.BACKENDS.keys()

    unread_count = 0
    user_bookmark_list = []
    if user_id:
        unread_count = NotificationModel().get_unread_cnt_for_user(user_id)
        user_bookmark_list = UserBookmark.get_bookmarks_for_user(user_id)
    context.unread_notifications = unread_count
    context.bookmark_items = user_bookmark_list

    # web case
    if hasattr(request, 'user'):
        context.auth_user = request.user
        context.rhodecode_user = request.user

    # api case
    if hasattr(request, 'rpc_user'):
        context.auth_user = request.rpc_user
        context.rhodecode_user = request.rpc_user

    # attach the whole call context to the request
    request.call_context = context


def get_auth_user(request):
    environ = request.environ
    session = request.session

    ip_addr = get_ip_addr(environ)

    # make sure that we update permissions each time we call controller
    _auth_token = (
            # ?auth_token=XXX
            request.GET.get('auth_token', '')
            # ?api_key=XXX !LEGACY
            or request.GET.get('api_key', '')
            # or headers....
            or request.headers.get('X-Rc-Auth-Token', '')
    )
    if not _auth_token and request.matchdict:
        url_auth_token = request.matchdict.get('_auth_token')
        _auth_token = url_auth_token
        if _auth_token:
            log.debug('Using URL extracted auth token `...%s`', _auth_token[-4:])

    if _auth_token:
        # when using API_KEY we assume user exists, and
        # doesn't need auth based on cookies.
        auth_user = AuthUser(api_key=_auth_token, ip_addr=ip_addr)
        authenticated = False
    else:
        cookie_store = CookieStoreWrapper(session.get('rhodecode_user'))
        try:
            auth_user = AuthUser(user_id=cookie_store.get('user_id', None),
                                 ip_addr=ip_addr)
        except UserCreationError as e:
            h.flash(e, 'error')
            # container auth or other auth functions that create users
            # on the fly can throw this exception signaling that there's
            # issue with user creation, explanation should be provided
            # in Exception itself. We then create a simple blank
            # AuthUser
            auth_user = AuthUser(ip_addr=ip_addr)

        # in case someone changes a password for user it triggers session
        # flush and forces a re-login
        if password_changed(auth_user, session):
            session.invalidate()
            cookie_store = CookieStoreWrapper(session.get('rhodecode_user'))
            auth_user = AuthUser(ip_addr=ip_addr)

        authenticated = cookie_store.get('is_authenticated')

    if not auth_user.is_authenticated and auth_user.is_user_object:
        # user is not authenticated and not empty
        auth_user.set_authenticated(authenticated)

    return auth_user, _auth_token


def h_filter(s):
    """
    Custom filter for Mako templates. Mako by standard uses `markupsafe.escape`
    we wrap this with additional functionality that converts None to empty
    strings
    """
    if s is None:
        return markupsafe.Markup()
    return markupsafe.escape(s)


def add_events_routes(config):
    """
    Adds routing that can be used in events. Because some events are triggered
    outside of pyramid context, we need to bootstrap request with some
    routing registered
    """

    from rhodecode.apps._base import ADMIN_PREFIX

    config.add_route(name='home', pattern='/')
    config.add_route(name='main_page_repos_data', pattern='/_home_repos')
    config.add_route(name='main_page_repo_groups_data', pattern='/_home_repo_groups')

    config.add_route(name='login', pattern=ADMIN_PREFIX + '/login')
    config.add_route(name='logout', pattern=ADMIN_PREFIX + '/logout')
    config.add_route(name='repo_summary', pattern='/{repo_name}')
    config.add_route(name='repo_summary_explicit', pattern='/{repo_name}/summary')
    config.add_route(name='repo_group_home', pattern='/{repo_group_name}')

    config.add_route(name='pullrequest_show',
                     pattern='/{repo_name}/pull-request/{pull_request_id}')
    config.add_route(name='pull_requests_global',
                     pattern='/pull-request/{pull_request_id}')

    config.add_route(name='repo_commit',
                     pattern='/{repo_name}/changeset/{commit_id}')
    config.add_route(name='repo_files',
                     pattern='/{repo_name}/files/{commit_id}/{f_path}')

    config.add_route(name='hovercard_user',
                     pattern='/_hovercard/user/{user_id}')

    config.add_route(name='hovercard_user_group',
                     pattern='/_hovercard/user_group/{user_group_id}')

    config.add_route(name='hovercard_pull_request',
                     pattern='/_hovercard/pull_request/{pull_request_id}')

    config.add_route(name='hovercard_repo_commit',
                     pattern='/_hovercard/commit/{repo_name}/{commit_id}')


def bootstrap_config(request):
    import pyramid.testing
    registry = pyramid.testing.Registry('RcTestRegistry')

    config = pyramid.testing.setUp(registry=registry, request=request)

    # allow pyramid lookup in testing
    config.include('pyramid_mako')
    config.include('rhodecode.lib.rc_beaker')
    config.include('rhodecode.lib.rc_cache')

    add_events_routes(config)

    return config


def bootstrap_request(**kwargs):
    import pyramid.testing

    class TestRequest(pyramid.testing.DummyRequest):
        application_url = kwargs.pop('application_url', 'http://example.com')
        host = kwargs.pop('host', 'example.com:80')
        domain = kwargs.pop('domain', 'example.com')

        def translate(self, msg):
            return msg

        def plularize(self, singular, plural, n):
            return singular

        def get_partial_renderer(self, tmpl_name):

            from rhodecode.lib.partial_renderer import get_partial_renderer
            return get_partial_renderer(request=self, tmpl_name=tmpl_name)

        _call_context = TemplateArgs()
        _call_context.visual = TemplateArgs()
        _call_context.visual.show_sha_length = 12
        _call_context.visual.show_revision_number = True

        @property
        def call_context(self):
            return self._call_context

    class TestDummySession(pyramid.testing.DummySession):
        def save(*arg, **kw):
            pass

    request = TestRequest(**kwargs)
    request.session = TestDummySession()

    return request

