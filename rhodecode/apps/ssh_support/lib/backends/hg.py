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
import shutil
import logging
import tempfile
import textwrap

from .base import VcsServer

log = logging.getLogger(__name__)


class MercurialTunnelWrapper(object):
    process = None

    def __init__(self, server):
        self.server = server
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.svn_conf_fd, self.svn_conf_path = tempfile.mkstemp()
        self.hooks_env_fd, self.hooks_env_path = tempfile.mkstemp()

    def create_hooks_env(self):

        content = textwrap.dedent(
            '''
            # SSH hooks version=1.0.0
            [hooks]
            pretxnchangegroup.ssh_auth=python:vcsserver.hooks.pre_push_ssh_auth
            pretxnchangegroup.ssh=python:vcsserver.hooks.pre_push_ssh
            changegroup.ssh=python:vcsserver.hooks.post_push_ssh
            
            preoutgoing.ssh=python:vcsserver.hooks.pre_pull_ssh
            outgoing.ssh=python:vcsserver.hooks.post_pull_ssh

            '''
        )

        with os.fdopen(self.hooks_env_fd, 'w') as hooks_env_file:
            hooks_env_file.write(content)
        root = self.server.get_root_store()

        hgrc_custom = os.path.join(
            root, self.server.repo_name, '.hg', 'hgrc_rhodecode')
        log.debug('Wrote custom hgrc file under %s', hgrc_custom)
        shutil.move(
            self.hooks_env_path, hgrc_custom)

        hgrc_main = os.path.join(
            root, self.server.repo_name, '.hg', 'hgrc')
        include_marker = '%include hgrc_rhodecode'

        if not os.path.isfile(hgrc_main):
            os.mknod(hgrc_main)

        with open(hgrc_main, 'rb') as f:
            data = f.read()
            has_marker = include_marker in data

        if not has_marker:
            log.debug('Adding include marker for hooks')
            with open(hgrc_main, 'wa') as f:
                f.write(textwrap.dedent('''
                # added by RhodeCode
                {}
                '''.format(include_marker)))

    def command(self):
        root = self.server.get_root_store()

        command = (
            "cd {root}; {hg_path} -R {root}{repo_name} "
            "serve --stdio".format(
                root=root, hg_path=self.server.hg_path,
                repo_name=self.server.repo_name))
        log.debug("Final CMD: %s", command)
        return command

    def run(self, extras):
        # at this point we cannot tell, we do further ACL checks
        # inside the hooks
        action = '?'
        # permissions are check via `pre_push_ssh_auth` hook
        self.server.update_environment(action=action, extras=extras)
        self.create_hooks_env()
        return os.system(self.command())


class MercurialServer(VcsServer):
    backend = 'hg'

    def __init__(self, store, ini_path, repo_name,
                 user, user_permissions, config, env):
        super(MercurialServer, self).\
            __init__(user, user_permissions, config, env)

        self.store = store
        self.ini_path = ini_path
        self.repo_name = repo_name
        self._path = self.hg_path = config.get(
            'app:main', 'ssh.executable.hg')

        self.tunnel = MercurialTunnelWrapper(server=self)
