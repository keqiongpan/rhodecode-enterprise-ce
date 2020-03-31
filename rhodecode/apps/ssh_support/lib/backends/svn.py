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
import re
import sys
import logging
import signal
import tempfile
from subprocess import Popen, PIPE
import urlparse

from .base import VcsServer

log = logging.getLogger(__name__)


class SubversionTunnelWrapper(object):
    process = None

    def __init__(self, server):
        self.server = server
        self.timeout = 30
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.svn_conf_fd, self.svn_conf_path = tempfile.mkstemp()
        self.hooks_env_fd, self.hooks_env_path = tempfile.mkstemp()

        self.read_only = True  # flag that we set to make the hooks readonly

    def create_svn_config(self):
        content = (
            '[general]\n'
            'hooks-env = {}\n').format(self.hooks_env_path)
        with os.fdopen(self.svn_conf_fd, 'w') as config_file:
            config_file.write(content)

    def create_hooks_env(self):
        content = (
            '[default]\n'
            'LANG = en_US.UTF-8\n')
        if self.read_only:
            content += 'SSH_READ_ONLY = 1\n'
        with os.fdopen(self.hooks_env_fd, 'w') as hooks_env_file:
            hooks_env_file.write(content)

    def remove_configs(self):
        os.remove(self.svn_conf_path)
        os.remove(self.hooks_env_path)

    def command(self):
        root = self.server.get_root_store()
        username = self.server.user.username

        command = [
            self.server.svn_path, '-t',
            '--config-file', self.svn_conf_path,
            '--tunnel-user', username,
            '-r', root]
        log.debug("Final CMD: %s", ' '.join(command))
        return command

    def start(self):
        command = self.command()
        self.process = Popen(' '.join(command), stdin=PIPE, shell=True)

    def sync(self):
        while self.process.poll() is None:
            next_byte = self.stdin.read(1)
            if not next_byte:
                break
            self.process.stdin.write(next_byte)
        self.remove_configs()

    @property
    def return_code(self):
        return self.process.returncode

    def get_first_client_response(self):
        signal.signal(signal.SIGALRM, self.interrupt)
        signal.alarm(self.timeout)
        first_response = self._read_first_client_response()
        signal.alarm(0)
        return (self._parse_first_client_response(first_response)
                if first_response else None)

    def patch_first_client_response(self, response, **kwargs):
        self.create_hooks_env()
        data = response.copy()
        data.update(kwargs)
        data['url'] = self._svn_string(data['url'])
        data['ra_client'] = self._svn_string(data['ra_client'])
        data['client'] = data['client'] or ''
        buffer_ = (
            "( {version} ( {capabilities} ) {url}{ra_client}"
            "( {client}) ) ".format(**data))
        self.process.stdin.write(buffer_)

    def fail(self, message):
        print("( failure ( ( 210005 {message} 0: 0 ) ) )".format(
            message=self._svn_string(message)))
        self.remove_configs()
        self.process.kill()
        return 1

    def interrupt(self, signum, frame):
        self.fail("Exited by timeout")

    def _svn_string(self, str_):
        if not str_:
            return ''
        return '{length}:{string} '.format(length=len(str_), string=str_)

    def _read_first_client_response(self):
        buffer_ = ""
        brackets_stack = []
        while True:
            next_byte = self.stdin.read(1)
            buffer_ += next_byte
            if next_byte == "(":
                brackets_stack.append(next_byte)
            elif next_byte == ")":
                brackets_stack.pop()
            elif next_byte == " " and not brackets_stack:
                break

        return buffer_

    def _parse_first_client_response(self, buffer_):
        """
        According to the Subversion RA protocol, the first request
        should look like:

        ( version:number ( cap:word ... ) url:string ? ra-client:string
           ( ? client:string ) )

        Please check https://svn.apache.org/repos/asf/subversion/trunk/subversion/libsvn_ra_svn/protocol
        """
        version_re = r'(?P<version>\d+)'
        capabilities_re = r'\(\s(?P<capabilities>[\w\d\-\ ]+)\s\)'
        url_re = r'\d+\:(?P<url>[\W\w]+)'
        ra_client_re = r'(\d+\:(?P<ra_client>[\W\w]+)\s)'
        client_re = r'(\d+\:(?P<client>[\W\w]+)\s)*'
        regex = re.compile(
            r'^\(\s{version}\s{capabilities}\s{url}\s{ra_client}'
            r'\(\s{client}\)\s\)\s*$'.format(
                version=version_re, capabilities=capabilities_re,
                url=url_re, ra_client=ra_client_re, client=client_re))
        matcher = regex.match(buffer_)

        return matcher.groupdict() if matcher else None

    def _match_repo_name(self, url):
        """
        Given an server url, try to match it against ALL known repository names.
        This handles a tricky SVN case for SSH and subdir commits.
        E.g if our repo name is my-svn-repo, a svn commit on file in a subdir would
        result in the url with this subdir added.
        """
        # case 1 direct match, we don't do any "heavy" lookups
        if url in self.server.user_permissions:
            return url

        log.debug('Extracting repository name from subdir path %s', url)
        # case 2 we check all permissions, and match closes possible case...
        # NOTE(dan): In this case we only know that url has a subdir parts, it's safe
        # to assume that it will have the repo name as prefix, we ensure the prefix
        # for similar repositories isn't matched by adding a /
        # e.g subgroup/repo-name/ and subgroup/repo-name-1/ would work correct.
        for repo_name in self.server.user_permissions:
            repo_name_prefix = repo_name + '/'
            if url.startswith(repo_name_prefix):
                log.debug('Found prefix %s match, returning proper repository name',
                          repo_name_prefix)
                return repo_name

        return

    def run(self, extras):
        action = 'pull'
        self.create_svn_config()
        self.start()

        first_response = self.get_first_client_response()
        if not first_response:
            return self.fail("Repository name cannot be extracted")

        url_parts = urlparse.urlparse(first_response['url'])

        self.server.repo_name = self._match_repo_name(url_parts.path.strip('/'))

        exit_code = self.server._check_permissions(action)
        if exit_code:
            return exit_code

        # set the readonly flag to False if we have proper permissions
        if self.server.has_write_perm():
            self.read_only = False
        self.server.update_environment(action=action, extras=extras)

        self.patch_first_client_response(first_response)
        self.sync()
        return self.return_code


class SubversionServer(VcsServer):
    backend = 'svn'

    def __init__(self, store, ini_path, repo_name,
                 user, user_permissions, config, env):
        super(SubversionServer, self)\
            .__init__(user, user_permissions, config, env)
        self.store = store
        self.ini_path = ini_path
        # NOTE(dan): repo_name at this point is empty,
        # this is set later in .run() based from parsed input stream
        self.repo_name = repo_name
        self._path = self.svn_path = config.get('app:main', 'ssh.executable.svn')

        self.tunnel = SubversionTunnelWrapper(server=self)

    def _handle_tunnel(self, extras):

        # pre-auth
        action = 'pull'
        # Special case for SVN, we extract repo name at later stage
        # exit_code = self._check_permissions(action)
        # if exit_code:
        #     return exit_code, False

        req = self.env['request']
        server_url = req.host_url + req.script_name
        extras['server_url'] = server_url

        log.debug('Using %s binaries from path %s', self.backend, self._path)
        exit_code = self.tunnel.run(extras)

        return exit_code, action == "push"


