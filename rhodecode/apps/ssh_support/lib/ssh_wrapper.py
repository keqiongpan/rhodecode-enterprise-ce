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

import click

from pyramid.paster import setup_logging

from rhodecode.lib.pyramid_utils import bootstrap
from .backends import SshWrapper

log = logging.getLogger(__name__)


def setup_custom_logging(ini_path, debug):
    if debug:
        # enabled rhodecode.ini controlled logging setup
        setup_logging(ini_path)
    else:
        # configure logging in a mode that doesn't print anything.
        # in case of regularly configured logging it gets printed out back
        # to the client doing an SSH command.
        logger = logging.getLogger('')
        null = logging.NullHandler()
        # add the handler to the root logger
        logger.handlers = [null]


@click.command()
@click.argument('ini_path', type=click.Path(exists=True))
@click.option(
    '--mode', '-m', required=False, default='auto',
    type=click.Choice(['auto', 'vcs', 'git', 'hg', 'svn', 'test']),
    help='mode of operation')
@click.option('--user', help='Username for which the command will be executed')
@click.option('--user-id', help='User ID for which the command will be executed')
@click.option('--key-id', help='ID of the key from the database')
@click.option('--shell', '-s', is_flag=True, help='Allow Shell')
@click.option('--debug', is_flag=True, help='Enabled detailed output logging')
def main(ini_path, mode, user, user_id, key_id, shell, debug):
    setup_custom_logging(ini_path, debug)

    command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    if not command and mode not in ['test']:
        raise ValueError(
            'Unable to fetch SSH_ORIGINAL_COMMAND from environment.'
            'Please make sure this is set and available during execution '
            'of this script.')
    connection_info = os.environ.get('SSH_CONNECTION', '')

    with bootstrap(ini_path, env={'RC_CMD_SSH_WRAPPER': '1'}) as env:
        try:
            ssh_wrapper = SshWrapper(
                command, connection_info, mode,
                user, user_id, key_id, shell, ini_path, env)
        except Exception:
            log.exception('Failed to execute SshWrapper')
            sys.exit(-5)

        return_code = ssh_wrapper.wrap()
        sys.exit(return_code)
