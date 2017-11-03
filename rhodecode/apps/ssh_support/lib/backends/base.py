# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 RhodeCode GmbH
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
import json
import logging

from rhodecode.lib.hooks_daemon import prepare_callback_daemon
from rhodecode.lib import hooks_utils
from rhodecode.model.scm import ScmModel

log = logging.getLogger(__name__)


class VcsServer(object):
    _path = None  # set executable path for hg/git/svn binary
    backend = None  # set in child classes
    tunnel = None  # subprocess handling tunnel
    write_perms = ['repository.admin', 'repository.write']
    read_perms = ['repository.read', 'repository.admin', 'repository.write']

    def __init__(self, user, user_permissions, config, env):
        self.user = user
        self.user_permissions = user_permissions
        self.config = config
        self.env = env
        self.stdin = sys.stdin

        self.repo_name = None
        self.repo_mode = None
        self.store = ''
        self.ini_path = ''

    def _invalidate_cache(self, repo_name):
        """
        Set's cache for this repository for invalidation on next access

        :param repo_name: full repo name, also a cache key
        """
        ScmModel().mark_for_invalidation(repo_name)

    def has_write_perm(self):
        permission = self.user_permissions.get(self.repo_name)
        if permission in ['repository.write', 'repository.admin']:
            return True

        return False

    def _check_permissions(self, action):
        permission = self.user_permissions.get(self.repo_name)
        log.debug(
            'permission for %s on %s are: %s',
            self.user, self.repo_name, permission)

        if action == 'pull':
            if permission in self.read_perms:
                log.info(
                    'READ Permissions for User "%s" detected to repo "%s"!',
                    self.user, self.repo_name)
                return 0
        else:
            if permission in self.write_perms:
                log.info(
                    'WRITE+ Permissions for User "%s" detected to repo "%s"!',
                    self.user, self.repo_name)
                return 0

        log.error('Cannot properly fetch or allow user %s permissions. '
                  'Return value is: %s, req action: %s',
                  self.user, permission, action)
        return -2

    def update_environment(self, action, extras=None):

        scm_data = {
            'ip': os.environ['SSH_CLIENT'].split()[0],
            'username': self.user.username,
            'action': action,
            'repository': self.repo_name,
            'scm': self.backend,
            'config': self.ini_path,
            'make_lock': None,
            'locked_by': [None, None],
            'server_url': None,
            'is_shadow_repo': False,
            'hooks_module': 'rhodecode.lib.hooks_daemon',
            'hooks': ['push', 'pull'],
            'SSH': True,
            'SSH_PERMISSIONS': self.user_permissions.get(self.repo_name)
        }
        if extras:
            scm_data.update(extras)
        os.putenv("RC_SCM_DATA", json.dumps(scm_data))

    def get_root_store(self):
        root_store = self.store
        if not root_store.endswith('/'):
            # always append trailing slash
            root_store = root_store + '/'
        return root_store

    def _handle_tunnel(self, extras):
        # pre-auth
        action = 'pull'
        exit_code = self._check_permissions(action)
        if exit_code:
            return exit_code, False

        req = self.env['request']
        server_url = req.host_url + req.script_name
        extras['server_url'] = server_url

        log.debug('Using %s binaries from path %s', self.backend, self._path)
        exit_code = self.tunnel.run(extras)

        return exit_code, action == "push"

    def run(self):
        extras = {}
        HOOKS_PROTOCOL = self.config.get('app:main', 'vcs.hooks.protocol')

        callback_daemon, extras = prepare_callback_daemon(
            extras, protocol=HOOKS_PROTOCOL,
            use_direct_calls=False)

        with callback_daemon:
            try:
                return self._handle_tunnel(extras)
            finally:
                log.debug('Running cleanup with cache invalidation')
                if self.repo_name:
                    self._invalidate_cache(self.repo_name)
