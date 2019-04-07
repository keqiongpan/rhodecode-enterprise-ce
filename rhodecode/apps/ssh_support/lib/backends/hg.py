# -*- coding: utf-8 -*-

# Copyright (C) 2016-2019 RhodeCode GmbH
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
import tempfile
import textwrap
import collections
from .base import VcsServer
from rhodecode.model.settings import VcsSettingsModel

log = logging.getLogger(__name__)


class MercurialTunnelWrapper(object):
    process = None

    def __init__(self, server):
        self.server = server
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.hooks_env_fd, self.hooks_env_path = tempfile.mkstemp(prefix='hgrc_rhodecode_')

    def create_hooks_env(self):
        repo_name = self.server.repo_name
        hg_flags = self.config_to_hgrc(repo_name)

        content = textwrap.dedent(
            '''
            # SSH hooks version=2.0.0
            [hooks]
            pretxnchangegroup.ssh_auth=python:vcsserver.hooks.pre_push_ssh_auth
            pretxnchangegroup.ssh=python:vcsserver.hooks.pre_push_ssh
            changegroup.ssh=python:vcsserver.hooks.post_push_ssh
            
            preoutgoing.ssh=python:vcsserver.hooks.pre_pull_ssh
            outgoing.ssh=python:vcsserver.hooks.post_pull_ssh

            # Custom Config version=2.0.0
            {custom}
            '''
        ).format(custom='\n'.join(hg_flags))

        root = self.server.get_root_store()
        hgrc_custom = os.path.join(root, repo_name, '.hg', 'hgrc_rhodecode')
        hgrc_main = os.path.join(root, repo_name, '.hg', 'hgrc')

        # cleanup custom hgrc file
        if os.path.isfile(hgrc_custom):
            with open(hgrc_custom, 'wb') as f:
                f.write('')
            log.debug('Cleanup custom hgrc file under %s', hgrc_custom)

        # write temp
        with os.fdopen(self.hooks_env_fd, 'w') as hooks_env_file:
            hooks_env_file.write(content)

        return self.hooks_env_path

    def remove_configs(self):
        os.remove(self.hooks_env_path)

    def command(self, hgrc_path):
        root = self.server.get_root_store()

        command = (
            "cd {root}; HGRCPATH={hgrc} {hg_path} -R {root}{repo_name} "
            "serve --stdio".format(
                root=root, hg_path=self.server.hg_path,
                repo_name=self.server.repo_name, hgrc=hgrc_path))
        log.debug("Final CMD: %s", command)
        return command

    def run(self, extras):
        # at this point we cannot tell, we do further ACL checks
        # inside the hooks
        action = '?'
        # permissions are check via `pre_push_ssh_auth` hook
        self.server.update_environment(action=action, extras=extras)
        custom_hgrc_file = self.create_hooks_env()

        try:
            return os.system(self.command(custom_hgrc_file))
        finally:
            self.remove_configs()


class MercurialServer(VcsServer):
    backend = 'hg'
    cli_flags = ['phases', 'largefiles', 'extensions', 'experimental']

    def __init__(self, store, ini_path, repo_name, user, user_permissions, config, env):
        super(MercurialServer, self).__init__(user, user_permissions, config, env)

        self.store = store
        self.ini_path = ini_path
        self.repo_name = repo_name
        self._path = self.hg_path = config.get('app:main', 'ssh.executable.hg')
        self.tunnel = MercurialTunnelWrapper(server=self)

    def config_to_hgrc(self, repo_name):
        ui_sections = collections.defaultdict(list)
        ui = VcsSettingsModel(repo=repo_name).get_ui_settings(section=None, key=None)

        for entry in ui:
            if not entry.active:
                continue
            sec = entry.section

            if sec in self.cli_flags:
                ui_sections[sec].append([entry.key, entry.value])

        flags = []
        for _sec, key_val in ui_sections.items():
            flags.append(' ')
            flags.append('[{}]'.format(_sec))
            for key, val in key_val:
                flags.append('{}= {}'.format(key, val))
        return flags
