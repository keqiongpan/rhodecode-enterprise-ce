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

import os
import re
import logging
import datetime
from pyramid.compat import configparser

from rhodecode.model.db import Session, User, UserSshKeys
from rhodecode.model.scm import ScmModel

from .hg import MercurialServer
from .git import GitServer
from .svn import SubversionServer
log = logging.getLogger(__name__)


class SshWrapper(object):
    hg_cmd_pat  = re.compile(r'^hg\s+\-R\s+(\S+)\s+serve\s+\-\-stdio$')
    git_cmd_pat = re.compile(r'^git-(receive-pack|upload-pack)\s\'[/]?(\S+?)(|\.git)\'$')
    svn_cmd_pat = re.compile(r'^svnserve -t')

    def __init__(self, command, connection_info, mode,
                 user, user_id, key_id, shell, ini_path, env):
        self.command = command
        self.connection_info = connection_info
        self.mode = mode
        self.user = user
        self.user_id = user_id
        self.key_id = key_id
        self.shell = shell
        self.ini_path = ini_path
        self.env = env

        self.config = self.parse_config(ini_path)
        self.server_impl = None

    def parse_config(self, config_path):
        parser = configparser.ConfigParser()
        parser.read(config_path)
        return parser

    def update_key_access_time(self, key_id):
        key = UserSshKeys().query().filter(
            UserSshKeys.ssh_key_id == key_id).scalar()
        if key:
            key.accessed_on = datetime.datetime.utcnow()
            Session().add(key)
            Session().commit()
            log.debug('Update key id:`%s` fingerprint:`%s` access time',
                      key_id, key.ssh_key_fingerprint)

    def get_connection_info(self):
        """
        connection_info

        Identifies the client and server ends of the connection.
        The variable contains four space-separated values: client IP address,
        client port number, server IP address, and server port number.
        """
        conn = dict(
            client_ip=None,
            client_port=None,
            server_ip=None,
            server_port=None,
        )

        info = self.connection_info.split(' ')
        if len(info) == 4:
            conn['client_ip'] = info[0]
            conn['client_port'] = info[1]
            conn['server_ip'] = info[2]
            conn['server_port'] = info[3]

        return conn

    def maybe_translate_repo_uid(self, repo_name):
        if repo_name.startswith('_'):
            from rhodecode.model.repo import RepoModel
            by_id_match = RepoModel().get_repo_by_id(repo_name)
            if by_id_match:
                repo_name = by_id_match.repo_name
        return repo_name

    def get_repo_details(self, mode):
        vcs_type = mode if mode in ['svn', 'hg', 'git'] else None
        repo_name = None

        hg_match = self.hg_cmd_pat.match(self.command)
        if hg_match is not None:
            vcs_type = 'hg'
            repo_name = self.maybe_translate_repo_uid(hg_match.group(1).strip('/'))
            return vcs_type, repo_name, mode

        git_match = self.git_cmd_pat.match(self.command)
        if git_match is not None:
            vcs_type = 'git'
            repo_name = self.maybe_translate_repo_uid(git_match.group(2).strip('/'))
            mode = git_match.group(1)
            return vcs_type, repo_name, mode

        svn_match = self.svn_cmd_pat.match(self.command)
        if svn_match is not None:
            vcs_type = 'svn'
            # Repo name should be extracted from the input stream, we're unable to
            # extract it at this point in execution
            return vcs_type, repo_name, mode

        return vcs_type, repo_name, mode

    def serve(self, vcs, repo, mode, user, permissions, branch_permissions):
        store = ScmModel().repos_path

        check_branch_perms = False
        detect_force_push = False

        if branch_permissions:
            check_branch_perms = True
            detect_force_push = True

        log.debug(
            'VCS detected:`%s` mode: `%s` repo_name: %s, branch_permission_checks:%s',
            vcs, mode, repo, check_branch_perms)

        # detect if we have to check branch permissions
        extras = {
            'detect_force_push': detect_force_push,
            'check_branch_perms': check_branch_perms,
        }

        if vcs == 'hg':
            server = MercurialServer(
                store=store, ini_path=self.ini_path,
                repo_name=repo, user=user,
                user_permissions=permissions, config=self.config, env=self.env)
            self.server_impl = server
            return server.run(tunnel_extras=extras)

        elif vcs == 'git':
            server = GitServer(
                store=store, ini_path=self.ini_path,
                repo_name=repo, repo_mode=mode, user=user,
                user_permissions=permissions, config=self.config, env=self.env)
            self.server_impl = server
            return server.run(tunnel_extras=extras)

        elif vcs == 'svn':
            server = SubversionServer(
                store=store, ini_path=self.ini_path,
                repo_name=None, user=user,
                user_permissions=permissions, config=self.config, env=self.env)
            self.server_impl = server
            return server.run(tunnel_extras=extras)

        else:
            raise Exception('Unrecognised VCS: {}'.format(vcs))

    def wrap(self):
        mode = self.mode
        user = self.user
        user_id = self.user_id
        key_id = self.key_id
        shell = self.shell

        scm_detected, scm_repo, scm_mode = self.get_repo_details(mode)

        log.debug(
            'Mode: `%s` User: `%s:%s` Shell: `%s` SSH Command: `\"%s\"` '
            'SCM_DETECTED: `%s` SCM Mode: `%s` SCM Repo: `%s`',
            mode, user, user_id, shell, self.command,
            scm_detected, scm_mode, scm_repo)

        # update last access time for this key
        self.update_key_access_time(key_id)

        log.debug('SSH Connection info %s', self.get_connection_info())

        if shell and self.command is None:
            log.info('Dropping to shell, no command given and shell is allowed')
            os.execl('/bin/bash', '-l')
            exit_code = 1

        elif scm_detected:
            user = User.get(user_id)
            if not user:
                log.warning('User with id %s not found', user_id)
                exit_code = -1
                return exit_code

            auth_user = user.AuthUser()
            permissions = auth_user.permissions['repositories']
            repo_branch_permissions = auth_user.get_branch_permissions(scm_repo)
            try:
                exit_code, is_updated = self.serve(
                    scm_detected, scm_repo, scm_mode, user, permissions,
                    repo_branch_permissions)
            except Exception:
                log.exception('Error occurred during execution of SshWrapper')
                exit_code = -1

        elif self.command is None and shell is False:
            log.error('No Command given.')
            exit_code = -1

        else:
            log.error('Unhandled Command: "%s" Aborting.', self.command)
            exit_code = -1

        return exit_code
