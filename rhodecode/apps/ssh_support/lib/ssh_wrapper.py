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
import re
import sys
import json
import logging
import random
import signal
import tempfile
from subprocess import Popen, PIPE, check_output, CalledProcessError
import ConfigParser
import urllib2
import urlparse

import click
import pyramid.paster


log = logging.getLogger(__name__)


def setup_logging(ini_path, debug):
    if debug:
        # enabled rhodecode.ini controlled logging setup
        pyramid.paster.setup_logging(ini_path)
    else:
        # configure logging in a mode that doesn't print anything.
        # in case of regularly configured logging it gets printed out back
        # to the client doing an SSH command.
        logger = logging.getLogger('')
        null = logging.NullHandler()
        # add the handler to the root logger
        logger.handlers = [null]


class SubversionTunnelWrapper(object):
    process = None

    def __init__(self, timeout, repositories_root=None, svn_path=None):
        self.timeout = timeout
        self.stdin = sys.stdin
        self.repositories_root = repositories_root
        self.svn_path = svn_path or 'svnserve'
        self.svn_conf_fd, self.svn_conf_path = tempfile.mkstemp()
        self.hooks_env_fd, self.hooks_env_path = tempfile.mkstemp()
        self.read_only = False
        self.create_svn_config()

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

    def start(self):
        config = ['--config-file', self.svn_conf_path]
        command = [self.svn_path, '-t'] + config
        if self.repositories_root:
            command.extend(['-r', self.repositories_root])
        self.process = Popen(command, stdin=PIPE)

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
        return (
            self._parse_first_client_response(first_response)
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
        print(
            "( failure ( ( 210005 {message} 0: 0 ) ) )".format(
                message=self._svn_string(message)))
        self.remove_configs()
        self.process.kill()

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

        Please check https://svn.apache.org/repos/asf/subversion/trunk/
           subversion/libsvn_ra_svn/protocol
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


class RhodeCodeApiClient(object):
    def __init__(self, api_key, api_host):
        self.api_key = api_key
        self.api_host = api_host

        if not api_host:
            raise ValueError('api_key:{} not defined'.format(api_key))
        if not api_host:
            raise ValueError('api_host:{} not defined '.format(api_host))

    def request(self, method, args):
        id_ = random.randrange(1, 9999)
        args = {
            'id': id_,
            'api_key': self.api_key,
            'method': method,
            'args': args
        }
        host = '{host}/_admin/api'.format(host=self.api_host)

        log.debug('Doing API call to %s method:%s', host, method)
        req = urllib2.Request(
            host,
            data=json.dumps(args),
            headers={'content-type': 'text/plain'})
        ret = urllib2.urlopen(req)
        raw_json = ret.read()
        json_data = json.loads(raw_json)
        id_ret = json_data['id']

        if id_ret != id_:
            raise Exception('something went wrong. '
                            'ID mismatch got %s, expected %s | %s'
                            % (id_ret, id_, raw_json))

        result = json_data['result']
        error = json_data['error']
        return result, error

    def get_user_permissions(self, user, user_id):
        result, error = self.request('get_user', {'userid': int(user_id)})
        if result is None and error:
            raise Exception(
                'User "%s" not found or another error happened: %s!' % (
                    user, error))
        log.debug(
            'Given User: `%s` Fetched User: `%s`', user, result.get('username'))
        return result.get('permissions').get('repositories')

    def invalidate_cache(self, repo_name):
        log.debug('Invalidate cache for repo:%s', repo_name)
        return self.request('invalidate_cache', {'repoid': repo_name})

    def get_repo_store(self):
        result, error = self.request('get_repo_store', {})
        return result


class VcsServer(object):

    def __init__(self, user, user_permissions, config):
        self.user = user
        self.user_permissions = user_permissions
        self.config = config
        self.repo_name = None
        self.repo_mode = None
        self.store = {}
        self.ini_path = ''

    def run(self):
        raise NotImplementedError()

    def get_root_store(self):
        root_store = self.store['path']
        if not root_store.endswith('/'):
            # always append trailing slash
            root_store = root_store + '/'
        return root_store


class MercurialServer(VcsServer):
    read_only = False

    def __init__(self, store, ini_path, repo_name,
                 user, user_permissions, config):
        super(MercurialServer, self).__init__(user, user_permissions, config)
        self.store = store
        self.repo_name = repo_name
        self.ini_path = ini_path
        self.hg_path = config.get('app:main', 'ssh.executable.hg')

    def run(self):
        if not self._check_permissions():
            return 2, False

        tip_before = self.tip()
        exit_code = os.system(self.command)
        tip_after = self.tip()
        return exit_code, tip_before != tip_after

    def tip(self):
        root = self.get_root_store()
        command = (
            'cd {root}; {hg_path} -R {root}{repo_name} tip --template "{{node}}\n"'
            ''.format(
                root=root, hg_path=self.hg_path, repo_name=self.repo_name))
        try:
            tip = check_output(command, shell=True).strip()
        except CalledProcessError:
            tip = None
        return tip

    @property
    def command(self):
        root = self.get_root_store()
        arguments = (
            '--config hooks.pretxnchangegroup=\"false\"'
            if self.read_only else '')

        command = (
            "cd {root}; {hg_path} -R {root}{repo_name} serve --stdio"
            " {arguments}".format(
                root=root, hg_path=self.hg_path, repo_name=self.repo_name,
                arguments=arguments))
        log.debug("Final CMD: %s", command)
        return command

    def _check_permissions(self):
        permission = self.user_permissions.get(self.repo_name)
        if permission is None or permission == 'repository.none':
            log.error('repo not found or no permissions')
            return False

        elif permission in ['repository.admin', 'repository.write']:
            log.info(
                'Write Permissions for User "%s" granted to repo "%s"!' % (
                    self.user, self.repo_name))
        else:
            self.read_only = True
            log.info(
                'Only Read Only access for User "%s" granted to repo "%s"!',
                self.user, self.repo_name)
        return True


class GitServer(VcsServer):
    def __init__(self, store, ini_path, repo_name, repo_mode,
                 user, user_permissions, config):
        super(GitServer, self).__init__(user, user_permissions, config)
        self.store = store
        self.ini_path = ini_path
        self.repo_name = repo_name
        self.repo_mode = repo_mode
        self.git_path = config.get('app:main', 'ssh.executable.git')

    def run(self):
        exit_code = self._check_permissions()
        if exit_code:
            return exit_code, False

        self._update_environment()
        exit_code = os.system(self.command)
        return exit_code, self.repo_mode == "receive-pack"

    @property
    def command(self):
        root = self.get_root_store()
        command = "cd {root}; {git_path}-{mode} '{root}{repo_name}'".format(
            root=root, git_path=self.git_path, mode=self.repo_mode,
            repo_name=self.repo_name)
        log.debug("Final CMD: %s", command)
        return command

    def _update_environment(self):
        action = "push" if self.repo_mode == "receive-pack" else "pull",
        scm_data = {
            "ip": os.environ["SSH_CLIENT"].split()[0],
            "username": self.user,
            "action": action,
            "repository": self.repo_name,
            "scm": "git",
            "config": self.ini_path,
            "make_lock": None,
            "locked_by": [None, None]
        }
        os.putenv("RC_SCM_DATA", json.dumps(scm_data))

    def _check_permissions(self):
        permission = self.user_permissions.get(self.repo_name)
        log.debug(
            'permission for %s on %s are: %s',
            self.user, self.repo_name, permission)

        if permission is None or permission == 'repository.none':
            log.error('repo not found or no permissions')
            return 2
        elif permission in ['repository.admin', 'repository.write']:
            log.info(
                'Write Permissions for User "%s" granted to repo "%s"!',
                self.user, self.repo_name)
        elif (permission == 'repository.read' and
                self.repo_mode == 'upload-pack'):
            log.info(
                'Only Read Only access for User "%s" granted to repo "%s"!',
                self.user, self.repo_name)
        elif (permission == 'repository.read'
                and self.repo_mode == 'receive-pack'):
            log.error(
                'Only Read Only access for User "%s" granted to repo "%s"!'
                ' Failing!', self.user, self.repo_name)
            return -3
        else:
            log.error('Cannot properly fetch user permission. '
                      'Return value is: %s', permission)
            return -2


class SubversionServer(VcsServer):

    def __init__(self, store, ini_path,
                 user, user_permissions, config):
        super(SubversionServer, self).__init__(user, user_permissions, config)
        self.store = store
        self.ini_path = ini_path
        # this is set in .run() from input stream
        self.repo_name = None
        self.svn_path = config.get('app:main', 'ssh.executable.svn')

    def run(self):
        root = self.get_root_store()
        log.debug("Using subversion binaries from '%s'", self.svn_path)

        self.tunnel = SubversionTunnelWrapper(
            timeout=self.timeout, repositories_root=root, svn_path=self.svn_path)
        self.tunnel.start()
        first_response = self.tunnel.get_first_client_response()
        if not first_response:
            self.tunnel.fail("Repository name cannot be extracted")
            return 1, False

        url_parts = urlparse.urlparse(first_response['url'])
        self.repo_name = url_parts.path.strip('/')
        if not self._check_permissions():
            self.tunnel.fail("Not enough permissions")
            return 1, False

        self.tunnel.patch_first_client_response(first_response)
        self.tunnel.sync()
        return self.tunnel.return_code, False

    @property
    def timeout(self):
        timeout = 30
        return timeout

    def _check_permissions(self):
        permission = self.user_permissions.get(self.repo_name)

        if permission in ['repository.admin', 'repository.write']:
            self.tunnel.read_only = False
            return True

        elif permission == 'repository.read':
            self.tunnel.read_only = True
            return True

        else:
            self.tunnel.fail("Not enough permissions for repository {}".format(
                self.repo_name))
            return False


class SshWrapper(object):

    def __init__(self, command, mode, user, user_id, shell, ini_path):
        self.command = command
        self.mode = mode
        self.user = user
        self.user_id = user_id
        self.shell = shell
        self.ini_path = ini_path

        self.config = self.parse_config(ini_path)
        api_key = self.config.get('app:main', 'ssh.api_key')
        api_host = self.config.get('app:main', 'ssh.api_host')
        self.api = RhodeCodeApiClient(api_key, api_host)

    def parse_config(self, config):
        parser = ConfigParser.ConfigParser()
        parser.read(config)
        return parser

    def get_repo_details(self, mode):
        type_ = mode if mode in ['svn', 'hg', 'git'] else None
        mode = mode
        name = None

        hg_pattern = r'^hg\s+\-R\s+(\S+)\s+serve\s+\-\-stdio$'
        hg_match = re.match(hg_pattern, self.command)
        if hg_match is not None:
            type_ = 'hg'
            name = hg_match.group(1).strip('/')
            return type_, name, mode

        git_pattern = (
            r'^git-(receive-pack|upload-pack)\s\'[/]?(\S+?)(|\.git)\'$')
        git_match = re.match(git_pattern, self.command)
        if git_match is not None:
            type_ = 'git'
            name = git_match.group(2).strip('/')
            mode = git_match.group(1)
            return type_, name, mode

        svn_pattern = r'^svnserve -t'
        svn_match = re.match(svn_pattern, self.command)
        if svn_match is not None:
            type_ = 'svn'
            # Repo name should be extracted from the input stream
            return type_, name, mode

        return type_, name, mode

    def serve(self, vcs, repo, mode, user, permissions):
        store = self.api.get_repo_store()

        log.debug(
            'VCS detected:`%s` mode: `%s` repo: %s', vcs, mode, repo)

        if vcs == 'hg':
            server = MercurialServer(
                store=store, ini_path=self.ini_path,
                repo_name=repo, user=user,
                user_permissions=permissions, config=self.config)
            return server.run()

        elif vcs == 'git':
            server = GitServer(
                store=store, ini_path=self.ini_path,
                repo_name=repo, repo_mode=mode, user=user,
                user_permissions=permissions, config=self.config)
            return server.run()

        elif vcs == 'svn':
            server = SubversionServer(
                store=store, ini_path=self.ini_path,
                user=user,
                user_permissions=permissions, config=self.config)
            return server.run()

        else:
            raise Exception('Unrecognised VCS: {}'.format(vcs))

    def wrap(self):
        mode = self.mode
        user = self.user
        user_id = self.user_id
        shell = self.shell

        scm_detected, scm_repo, scm_mode = self.get_repo_details(mode)
        log.debug(
            'Mode: `%s` User: `%s:%s` Shell: `%s` SSH Command: `\"%s\"` '
            'SCM_DETECTED: `%s` SCM Mode: `%s` SCM Repo: `%s`',
            mode, user, user_id, shell, self.command,
            scm_detected, scm_mode, scm_repo)

        try:
            permissions = self.api.get_user_permissions(user, user_id)
        except Exception as e:
            log.exception('Failed to fetch user permissions')
            return 1

        if shell and self.command is None:
            log.info(
                'Dropping to shell, no command given and shell is allowed')
            os.execl('/bin/bash', '-l')
            exit_code = 1

        elif scm_detected:
            try:
                exit_code, is_updated = self.serve(
                    scm_detected, scm_repo, scm_mode, user, permissions)
                if exit_code == 0 and is_updated:
                    self.api.invalidate_cache(scm_repo)
            except Exception:
                log.exception('Error occurred during execution of SshWrapper')
                exit_code = -1

        elif self.command is None and shell is False:
            log.error('No Command given.')
            exit_code = -1

        else:
            log.error(
                'Unhandled Command: "%s" Aborting.', self.command)
            exit_code = -1

        return exit_code


@click.command()
@click.argument('ini_path', type=click.Path(exists=True))
@click.option(
    '--mode', '-m', required=False, default='auto',
    type=click.Choice(['auto', 'vcs', 'git', 'hg', 'svn', 'test']),
    help='mode of operation')
@click.option('--user', help='Username for which the command will be executed')
@click.option('--user-id', help='User ID for which the command will be executed')
@click.option('--shell', '-s', is_flag=True, help='Allow Shell')
@click.option('--debug', is_flag=True, help='Enabled detailed output logging')
def main(ini_path, mode, user, user_id, shell, debug):
    setup_logging(ini_path, debug)

    command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    if not command and mode not in ['test']:
        raise ValueError(
            'Unable to fetch SSH_ORIGINAL_COMMAND from environment.'
            'Please make sure this is set and available during execution '
            'of this script.')

    try:
        ssh_wrapper = SshWrapper(command, mode, user, user_id, shell, ini_path)
    except Exception:
        log.exception('Failed to execute SshWrapper')
        sys.exit(-5)

    sys.exit(ssh_wrapper.wrap())