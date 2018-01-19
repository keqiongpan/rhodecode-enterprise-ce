# -*- coding: utf-8 -*-

# Copyright (C) 2016-2018 RhodeCode GmbH
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

from .base import VcsServer

log = logging.getLogger(__name__)


class GitTunnelWrapper(object):
    process = None

    def __init__(self, server):
        self.server = server
        self.stdin = sys.stdin
        self.stdout = sys.stdout

    def create_hooks_env(self):
        pass

    def command(self):
        root = self.server.get_root_store()
        command = "cd {root}; {git_path} {mode} '{root}{repo_name}'".format(
            root=root, git_path=self.server.git_path,
            mode=self.server.repo_mode, repo_name=self.server.repo_name)
        log.debug("Final CMD: %s", command)
        return command

    def run(self, extras):
        action = "push" if self.server.repo_mode == "receive-pack" else "pull"
        exit_code = self.server._check_permissions(action)
        if exit_code:
            return exit_code

        self.server.update_environment(action=action, extras=extras)
        self.create_hooks_env()
        return os.system(self.command())


class GitServer(VcsServer):
    backend = 'git'

    def __init__(self, store, ini_path, repo_name, repo_mode,
                 user, user_permissions, config, env):
        super(GitServer, self).\
            __init__(user, user_permissions, config, env)

        self.store = store
        self.ini_path = ini_path
        self.repo_name = repo_name
        self._path = self.git_path = config.get(
            'app:main', 'ssh.executable.git')

        self.repo_mode = repo_mode
        self.tunnel = GitTunnelWrapper(server=self)
