# -*- coding: utf-8 -*-

# Copyright (C) 2014-2018 RhodeCode GmbH
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
SimpleVCS middleware for handling protocol request (push/clone etc.)
It's implemented with basic auth function
"""

import os
import re
import logging
import importlib
from functools import wraps
from StringIO import StringIO
from lxml import etree

import time
from paste.httpheaders import REMOTE_USER, AUTH_TYPE

from pyramid.httpexceptions import (
    HTTPNotFound, HTTPForbidden, HTTPNotAcceptable, HTTPInternalServerError)
from zope.cachedescriptors.property import Lazy as LazyProperty

import rhodecode
from rhodecode.authentication.base import (
    authenticate, get_perms_cache_manager, VCS_TYPE, loadplugin)
from rhodecode.lib import caches
from rhodecode.lib.auth import AuthUser, HasPermissionAnyMiddleware
from rhodecode.lib.base import (
    BasicAuth, get_ip_addr, get_user_agent, vcs_operation_context)
from rhodecode.lib.exceptions import (UserCreationError, NotAllowedToCreateUserError)
from rhodecode.lib.hooks_daemon import prepare_callback_daemon
from rhodecode.lib.middleware import appenlight
from rhodecode.lib.middleware.utils import scm_app_http
from rhodecode.lib.utils import is_valid_repo, SLUG_RE
from rhodecode.lib.utils2 import safe_str, fix_PATH, str2bool, safe_unicode
from rhodecode.lib.vcs.conf import settings as vcs_settings
from rhodecode.lib.vcs.backends import base

from rhodecode.model import meta
from rhodecode.model.db import User, Repository, PullRequest
from rhodecode.model.scm import ScmModel
from rhodecode.model.pull_request import PullRequestModel
from rhodecode.model.settings import SettingsModel, VcsSettingsModel

log = logging.getLogger(__name__)


def extract_svn_txn_id(acl_repo_name, data):
    """
    Helper method for extraction of svn txn_id from submited XML data during
    POST operations
    """
    try:
        root = etree.fromstring(data)
        pat = re.compile(r'/txn/(?P<txn_id>.*)')
        for el in root:
            if el.tag == '{DAV:}source':
                for sub_el in el:
                    if sub_el.tag == '{DAV:}href':
                        match = pat.search(sub_el.text)
                        if match:
                            svn_tx_id = match.groupdict()['txn_id']
                            txn_id = caches.compute_key_from_params(
                                acl_repo_name, svn_tx_id)
                            return txn_id
    except Exception:
        log.exception('Failed to extract txn_id')


def initialize_generator(factory):
    """
    Initializes the returned generator by draining its first element.

    This can be used to give a generator an initializer, which is the code
    up to the first yield statement. This decorator enforces that the first
    produced element has the value ``"__init__"`` to make its special
    purpose very explicit in the using code.
    """

    @wraps(factory)
    def wrapper(*args, **kwargs):
        gen = factory(*args, **kwargs)
        try:
            init = gen.next()
        except StopIteration:
            raise ValueError('Generator must yield at least one element.')
        if init != "__init__":
            raise ValueError('First yielded element must be "__init__".')
        return gen
    return wrapper


class SimpleVCS(object):
    """Common functionality for SCM HTTP handlers."""

    SCM = 'unknown'

    acl_repo_name = None
    url_repo_name = None
    vcs_repo_name = None
    rc_extras = {}

    # We have to handle requests to shadow repositories different than requests
    # to normal repositories. Therefore we have to distinguish them. To do this
    # we use this regex which will match only on URLs pointing to shadow
    # repositories.
    shadow_repo_re = re.compile(
        '(?P<groups>(?:{slug_pat}/)*)'  # repo groups
        '(?P<target>{slug_pat})/'       # target repo
        'pull-request/(?P<pr_id>\d+)/'  # pull request
        'repository$'                   # shadow repo
        .format(slug_pat=SLUG_RE.pattern))

    def __init__(self, config, registry):
        self.registry = registry
        self.config = config
        # re-populated by specialized middleware
        self.repo_vcs_config = base.Config()
        self.rhodecode_settings = SettingsModel().get_all_settings(cache=True)

        registry.rhodecode_settings = self.rhodecode_settings
        # authenticate this VCS request using authfunc
        auth_ret_code_detection = \
            str2bool(self.config.get('auth_ret_code_detection', False))
        self.authenticate = BasicAuth(
            '', authenticate, registry, config.get('auth_ret_code'),
            auth_ret_code_detection)
        self.ip_addr = '0.0.0.0'

    @LazyProperty
    def global_vcs_config(self):
        try:
            return VcsSettingsModel().get_ui_settings_as_config_obj()
        except Exception:
            return base.Config()

    @property
    def base_path(self):
        settings_path = self.repo_vcs_config.get(
            *VcsSettingsModel.PATH_SETTING)

        if not settings_path:
            settings_path = self.global_vcs_config.get(
            *VcsSettingsModel.PATH_SETTING)

        if not settings_path:
            # try, maybe we passed in explicitly as config option
            settings_path = self.config.get('base_path')

        if not settings_path:
            raise ValueError('FATAL: base_path is empty')
        return settings_path

    def set_repo_names(self, environ):
        """
        This will populate the attributes acl_repo_name, url_repo_name,
        vcs_repo_name and is_shadow_repo. In case of requests to normal (non
        shadow) repositories all names are equal. In case of requests to a
        shadow repository the acl-name points to the target repo of the pull
        request and the vcs-name points to the shadow repo file system path.
        The url-name is always the URL used by the vcs client program.

        Example in case of a shadow repo:
            acl_repo_name = RepoGroup/MyRepo
            url_repo_name = RepoGroup/MyRepo/pull-request/3/repository
            vcs_repo_name = /repo/base/path/RepoGroup/.__shadow_MyRepo_pr-3'
        """
        # First we set the repo name from URL for all attributes. This is the
        # default if handling normal (non shadow) repo requests.
        self.url_repo_name = self._get_repository_name(environ)
        self.acl_repo_name = self.vcs_repo_name = self.url_repo_name
        self.is_shadow_repo = False

        # Check if this is a request to a shadow repository.
        match = self.shadow_repo_re.match(self.url_repo_name)
        if match:
            match_dict = match.groupdict()

            # Build acl repo name from regex match.
            acl_repo_name = safe_unicode('{groups}{target}'.format(
                groups=match_dict['groups'] or '',
                target=match_dict['target']))

            # Retrieve pull request instance by ID from regex match.
            pull_request = PullRequest.get(match_dict['pr_id'])

            # Only proceed if we got a pull request and if acl repo name from
            # URL equals the target repo name of the pull request.
            if pull_request and \
                    (acl_repo_name == pull_request.target_repo.repo_name):
                repo_id = pull_request.target_repo.repo_id
                # Get file system path to shadow repository.
                workspace_id = PullRequestModel()._workspace_id(pull_request)
                target_vcs = pull_request.target_repo.scm_instance()
                vcs_repo_name = target_vcs._get_shadow_repository_path(
                    repo_id, workspace_id)

                # Store names for later usage.
                self.vcs_repo_name = vcs_repo_name
                self.acl_repo_name = acl_repo_name
                self.is_shadow_repo = True

        log.debug('Setting all VCS repository names: %s', {
            'acl_repo_name': self.acl_repo_name,
            'url_repo_name': self.url_repo_name,
            'vcs_repo_name': self.vcs_repo_name,
        })

    @property
    def scm_app(self):
        custom_implementation = self.config['vcs.scm_app_implementation']
        if custom_implementation == 'http':
            log.info('Using HTTP implementation of scm app.')
            scm_app_impl = scm_app_http
        else:
            log.info('Using custom implementation of scm_app: "{}"'.format(
                custom_implementation))
            scm_app_impl = importlib.import_module(custom_implementation)
        return scm_app_impl

    def _get_by_id(self, repo_name):
        """
        Gets a special pattern _<ID> from clone url and tries to replace it
        with a repository_name for support of _<ID> non changeable urls
        """

        data = repo_name.split('/')
        if len(data) >= 2:
            from rhodecode.model.repo import RepoModel
            by_id_match = RepoModel().get_repo_by_id(repo_name)
            if by_id_match:
                data[1] = by_id_match.repo_name

        return safe_str('/'.join(data))

    def _invalidate_cache(self, repo_name):
        """
        Set's cache for this repository for invalidation on next access

        :param repo_name: full repo name, also a cache key
        """
        ScmModel().mark_for_invalidation(repo_name)

    def is_valid_and_existing_repo(self, repo_name, base_path, scm_type):
        db_repo = Repository.get_by_repo_name(repo_name)
        if not db_repo:
            log.debug('Repository `%s` not found inside the database.',
                      repo_name)
            return False

        if db_repo.repo_type != scm_type:
            log.warning(
                'Repository `%s` have incorrect scm_type, expected %s got %s',
                repo_name, db_repo.repo_type, scm_type)
            return False

        config = db_repo._config
        config.set('extensions', 'largefiles', '')
        return is_valid_repo(
            repo_name, base_path,
            explicit_scm=scm_type, expect_scm=scm_type, config=config)

    def valid_and_active_user(self, user):
        """
        Checks if that user is not empty, and if it's actually object it checks
        if he's active.

        :param user: user object or None
        :return: boolean
        """
        if user is None:
            return False

        elif user.active:
            return True

        return False

    @property
    def is_shadow_repo_dir(self):
        return os.path.isdir(self.vcs_repo_name)

    def _check_permission(self, action, user, repo_name, ip_addr=None,
                          plugin_id='', plugin_cache_active=False, cache_ttl=0):
        """
        Checks permissions using action (push/pull) user and repository
        name. If plugin_cache and ttl is set it will use the plugin which
        authenticated the user to store the cached permissions result for N
        amount of seconds as in cache_ttl

        :param action: push or pull action
        :param user: user instance
        :param repo_name: repository name
        """

        # get instance of cache manager configured for a namespace
        cache_manager = get_perms_cache_manager(
            custom_ttl=cache_ttl, suffix=user.user_id)
        log.debug('AUTH_CACHE_TTL for permissions `%s` active: %s (TTL: %s)',
                  plugin_id, plugin_cache_active, cache_ttl)

        # for environ based password can be empty, but then the validation is
        # on the server that fills in the env data needed for authentication
        _perm_calc_hash = caches.compute_key_from_params(
            plugin_id, action, user.user_id, repo_name, ip_addr)

        # _authenticate is a wrapper for .auth() method of plugin.
        # it checks if .auth() sends proper data.
        # For RhodeCodeExternalAuthPlugin it also maps users to
        # Database and maps the attributes returned from .auth()
        # to RhodeCode database. If this function returns data
        # then auth is correct.
        start = time.time()
        log.debug('Running plugin `%s` permissions check', plugin_id)

        def perm_func():
            """
            This function is used internally in Cache of Beaker to calculate
            Results
            """
            log.debug('auth: calculating permission access now...')
            # check IP
            inherit = user.inherit_default_permissions
            ip_allowed = AuthUser.check_ip_allowed(
                user.user_id, ip_addr, inherit_from_default=inherit)
            if ip_allowed:
                log.info('Access for IP:%s allowed', ip_addr)
            else:
                return False

            if action == 'push':
                perms = ('repository.write', 'repository.admin')
                if not HasPermissionAnyMiddleware(*perms)(user, repo_name):
                    return False

            else:
                # any other action need at least read permission
                perms = (
                    'repository.read', 'repository.write', 'repository.admin')
                if not HasPermissionAnyMiddleware(*perms)(user, repo_name):
                    return False

            return True

        if plugin_cache_active:
            log.debug('Trying to fetch cached perms by %s', _perm_calc_hash[:6])
            perm_result = cache_manager.get(
                _perm_calc_hash, createfunc=perm_func)
        else:
            perm_result = perm_func()

        auth_time = time.time() - start
        log.debug('Permissions for plugin `%s` completed in %.3fs, '
                  'expiration time of fetched cache %.1fs.',
                  plugin_id, auth_time, cache_ttl)

        return perm_result

    def _check_ssl(self, environ, start_response):
        """
        Checks the SSL check flag and returns False if SSL is not present
        and required True otherwise
        """
        org_proto = environ['wsgi._org_proto']
        # check if we have SSL required  ! if not it's a bad request !
        require_ssl = str2bool(self.repo_vcs_config.get('web', 'push_ssl'))
        if require_ssl and org_proto == 'http':
            log.debug(
                'Bad request: detected protocol is `%s` and '
                'SSL/HTTPS is required.', org_proto)
            return False
        return True

    def _get_default_cache_ttl(self):
        # take AUTH_CACHE_TTL from the `rhodecode` auth plugin
        plugin = loadplugin('egg:rhodecode-enterprise-ce#rhodecode')
        plugin_settings = plugin.get_settings()
        plugin_cache_active, cache_ttl = plugin.get_ttl_cache(
            plugin_settings) or (False, 0)
        return plugin_cache_active, cache_ttl

    def __call__(self, environ, start_response):
        try:
            return self._handle_request(environ, start_response)
        except Exception:
            log.exception("Exception while handling request")
            appenlight.track_exception(environ)
            return HTTPInternalServerError()(environ, start_response)
        finally:
            meta.Session.remove()

    def _handle_request(self, environ, start_response):

        if not self._check_ssl(environ, start_response):
            reason = ('SSL required, while RhodeCode was unable '
                      'to detect this as SSL request')
            log.debug('User not allowed to proceed, %s', reason)
            return HTTPNotAcceptable(reason)(environ, start_response)

        if not self.url_repo_name:
            log.warning('Repository name is empty: %s', self.url_repo_name)
            # failed to get repo name, we fail now
            return HTTPNotFound()(environ, start_response)
        log.debug('Extracted repo name is %s', self.url_repo_name)

        ip_addr = get_ip_addr(environ)
        user_agent = get_user_agent(environ)
        username = None

        # skip passing error to error controller
        environ['pylons.status_code_redirect'] = True

        # ======================================================================
        # GET ACTION PULL or PUSH
        # ======================================================================
        action = self._get_action(environ)

        # ======================================================================
        # Check if this is a request to a shadow repository of a pull request.
        # In this case only pull action is allowed.
        # ======================================================================
        if self.is_shadow_repo and action != 'pull':
            reason = 'Only pull action is allowed for shadow repositories.'
            log.debug('User not allowed to proceed, %s', reason)
            return HTTPNotAcceptable(reason)(environ, start_response)

        # Check if the shadow repo actually exists, in case someone refers
        # to it, and it has been deleted because of successful merge.
        if self.is_shadow_repo and not self.is_shadow_repo_dir:
            log.debug(
                'Shadow repo detected, and shadow repo dir `%s` is missing',
                self.is_shadow_repo_dir)
            return HTTPNotFound()(environ, start_response)

        # ======================================================================
        # CHECK ANONYMOUS PERMISSION
        # ======================================================================
        if action in ['pull', 'push']:
            anonymous_user = User.get_default_user()
            username = anonymous_user.username
            if anonymous_user.active:
                plugin_cache_active, cache_ttl = self._get_default_cache_ttl()
                # ONLY check permissions if the user is activated
                anonymous_perm = self._check_permission(
                    action, anonymous_user, self.acl_repo_name, ip_addr,
                    plugin_id='anonymous_access',
                    plugin_cache_active=plugin_cache_active,
                    cache_ttl=cache_ttl,
                )
            else:
                anonymous_perm = False

            if not anonymous_user.active or not anonymous_perm:
                if not anonymous_user.active:
                    log.debug('Anonymous access is disabled, running '
                              'authentication')

                if not anonymous_perm:
                    log.debug('Not enough credentials to access this '
                              'repository as anonymous user')

                username = None
                # ==============================================================
                # DEFAULT PERM FAILED OR ANONYMOUS ACCESS IS DISABLED SO WE
                # NEED TO AUTHENTICATE AND ASK FOR AUTH USER PERMISSIONS
                # ==============================================================

                # try to auth based on environ, container auth methods
                log.debug('Running PRE-AUTH for container based authentication')
                pre_auth = authenticate(
                    '', '', environ, VCS_TYPE, registry=self.registry,
                    acl_repo_name=self.acl_repo_name)
                if pre_auth and pre_auth.get('username'):
                    username = pre_auth['username']
                log.debug('PRE-AUTH got %s as username', username)
                if pre_auth:
                    log.debug('PRE-AUTH successful from %s',
                              pre_auth.get('auth_data', {}).get('_plugin'))

                # If not authenticated by the container, running basic auth
                # before inject the calling repo_name for special scope checks
                self.authenticate.acl_repo_name = self.acl_repo_name

                plugin_cache_active, cache_ttl = False, 0
                plugin = None
                if not username:
                    self.authenticate.realm = self.authenticate.get_rc_realm()

                    try:
                        auth_result = self.authenticate(environ)
                    except (UserCreationError, NotAllowedToCreateUserError) as e:
                        log.error(e)
                        reason = safe_str(e)
                        return HTTPNotAcceptable(reason)(environ, start_response)

                    if isinstance(auth_result, dict):
                        AUTH_TYPE.update(environ, 'basic')
                        REMOTE_USER.update(environ, auth_result['username'])
                        username = auth_result['username']
                        plugin = auth_result.get('auth_data', {}).get('_plugin')
                        log.info(
                            'MAIN-AUTH successful for user `%s` from %s plugin',
                            username, plugin)

                        plugin_cache_active, cache_ttl = auth_result.get(
                            'auth_data', {}).get('_ttl_cache') or (False, 0)
                    else:
                        return auth_result.wsgi_application(
                            environ, start_response)


                # ==============================================================
                # CHECK PERMISSIONS FOR THIS REQUEST USING GIVEN USERNAME
                # ==============================================================
                user = User.get_by_username(username)
                if not self.valid_and_active_user(user):
                    return HTTPForbidden()(environ, start_response)
                username = user.username
                user.update_lastactivity()
                meta.Session().commit()

                # check user attributes for password change flag
                user_obj = user
                if user_obj and user_obj.username != User.DEFAULT_USER and \
                        user_obj.user_data.get('force_password_change'):
                    reason = 'password change required'
                    log.debug('User not allowed to authenticate, %s', reason)
                    return HTTPNotAcceptable(reason)(environ, start_response)

                # check permissions for this repository
                perm = self._check_permission(
                    action, user, self.acl_repo_name, ip_addr,
                    plugin, plugin_cache_active, cache_ttl)
                if not perm:
                    return HTTPForbidden()(environ, start_response)

        # extras are injected into UI object and later available
        # in hooks executed by RhodeCode
        check_locking = _should_check_locking(environ.get('QUERY_STRING'))
        extras = vcs_operation_context(
            environ, repo_name=self.acl_repo_name, username=username,
            action=action, scm=self.SCM, check_locking=check_locking,
            is_shadow_repo=self.is_shadow_repo
        )

        # ======================================================================
        # REQUEST HANDLING
        # ======================================================================
        repo_path = os.path.join(
            safe_str(self.base_path), safe_str(self.vcs_repo_name))
        log.debug('Repository path is %s', repo_path)

        fix_PATH()

        log.info(
            '%s action on %s repo "%s" by "%s" from %s %s',
            action, self.SCM, safe_str(self.url_repo_name),
            safe_str(username), ip_addr, user_agent)

        return self._generate_vcs_response(
            environ, start_response, repo_path, extras, action)

    @initialize_generator
    def _generate_vcs_response(
            self, environ, start_response, repo_path, extras, action):
        """
        Returns a generator for the response content.

        This method is implemented as a generator, so that it can trigger
        the cache validation after all content sent back to the client. It
        also handles the locking exceptions which will be triggered when
        the first chunk is produced by the underlying WSGI application.
        """
        txn_id = ''
        if 'CONTENT_LENGTH' in environ and environ['REQUEST_METHOD'] == 'MERGE':
            # case for SVN, we want to re-use the callback daemon port
            # so we use the txn_id, for this we peek the body, and still save
            # it as wsgi.input
            data = environ['wsgi.input'].read()
            environ['wsgi.input'] = StringIO(data)
            txn_id = extract_svn_txn_id(self.acl_repo_name, data)

        callback_daemon, extras = self._prepare_callback_daemon(
            extras, environ, action, txn_id=txn_id)
        log.debug('HOOKS extras is %s', extras)

        config = self._create_config(extras, self.acl_repo_name)
        app = self._create_wsgi_app(repo_path, self.url_repo_name, config)
        with callback_daemon:
            app.rc_extras = extras

            try:
                response = app(environ, start_response)
            finally:
                # This statement works together with the decorator
                # "initialize_generator" above. The decorator ensures that
                # we hit the first yield statement before the generator is
                # returned back to the WSGI server. This is needed to
                # ensure that the call to "app" above triggers the
                # needed callback to "start_response" before the
                # generator is actually used.
                yield "__init__"

            # iter content
            for chunk in response:
                yield chunk

            try:
                # invalidate cache on push
                if action == 'push':
                    self._invalidate_cache(self.url_repo_name)
            finally:
                meta.Session.remove()

    def _get_repository_name(self, environ):
        """Get repository name out of the environmnent

        :param environ: WSGI environment
        """
        raise NotImplementedError()

    def _get_action(self, environ):
        """Map request commands into a pull or push command.

        :param environ: WSGI environment
        """
        raise NotImplementedError()

    def _create_wsgi_app(self, repo_path, repo_name, config):
        """Return the WSGI app that will finally handle the request."""
        raise NotImplementedError()

    def _create_config(self, extras, repo_name):
        """Create a safe config representation."""
        raise NotImplementedError()

    def _should_use_callback_daemon(self, extras, environ, action):
        return True

    def _prepare_callback_daemon(self, extras, environ, action, txn_id=None):
        direct_calls = vcs_settings.HOOKS_DIRECT_CALLS
        if not self._should_use_callback_daemon(extras, environ, action):
            # disable callback daemon for actions that don't require it
            direct_calls = True

        return prepare_callback_daemon(
            extras, protocol=vcs_settings.HOOKS_PROTOCOL,
            use_direct_calls=direct_calls, txn_id=txn_id)


def _should_check_locking(query_string):
    # this is kind of hacky, but due to how mercurial handles client-server
    # server see all operation on commit; bookmarks, phases and
    # obsolescence marker in different transaction, we don't want to check
    # locking on those
    return query_string not in ['cmd=listkeys']
