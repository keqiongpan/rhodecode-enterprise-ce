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
import stat
import logging
import tempfile
import datetime

from . import config_keys
from rhodecode.model.db import true, joinedload, User, UserSshKeys


log = logging.getLogger(__name__)

HEADER = \
    "# This file is managed by RhodeCode, please do not edit it manually. # \n" \
    "# Current entries: {}, create date: UTC:{}.\n"

# Default SSH options for authorized_keys file, can be override via .ini
SSH_OPTS = 'no-pty,no-port-forwarding,no-X11-forwarding,no-agent-forwarding'


def get_all_active_keys():
    result = UserSshKeys.query() \
        .options(joinedload(UserSshKeys.user)) \
        .filter(UserSshKeys.user != User.get_default_user()) \
        .filter(User.active == true()) \
        .all()
    return result


def _generate_ssh_authorized_keys_file(
        authorized_keys_file_path, ssh_wrapper_cmd, allow_shell, ssh_opts, debug):

    authorized_keys_file_path = os.path.abspath(
        os.path.expanduser(authorized_keys_file_path))

    import rhodecode
    all_active_keys = get_all_active_keys()

    if allow_shell:
        ssh_wrapper_cmd = ssh_wrapper_cmd + ' --shell'
    if debug:
        ssh_wrapper_cmd = ssh_wrapper_cmd + ' --debug'

    if not os.path.isfile(authorized_keys_file_path):
        log.debug('Creating file at %s', authorized_keys_file_path)
        with open(authorized_keys_file_path, 'w'):
            pass

    if not os.access(authorized_keys_file_path, os.R_OK):
        raise OSError('Access to file {} is without read access'.format(
            authorized_keys_file_path))

    line_tmpl = '{ssh_opts},command="{wrapper_command} {ini_path} --user-id={user_id} --user={user} --key-id={user_key_id}" {key}\n'

    fd, tmp_authorized_keys = tempfile.mkstemp(
        '.authorized_keys_write',
        dir=os.path.dirname(authorized_keys_file_path))

    now = datetime.datetime.utcnow().isoformat()
    keys_file = os.fdopen(fd, 'wb')
    keys_file.write(HEADER.format(len(all_active_keys), now))
    ini_path = rhodecode.CONFIG['__file__']

    for user_key in all_active_keys:
        username = user_key.user.username
        user_id = user_key.user.user_id
        # replace all newline from ends and inside
        safe_key_data = user_key.ssh_key_data\
            .strip()\
            .replace('\n', ' ') \
            .replace('\t', ' ') \
            .replace('\r', ' ')

        line = line_tmpl.format(
            ssh_opts=ssh_opts or SSH_OPTS,
            wrapper_command=ssh_wrapper_cmd,
            ini_path=ini_path,
            user_id=user_id,
            user=username,
            user_key_id=user_key.ssh_key_id,
            key=safe_key_data)

        keys_file.write(line)
        log.debug('addkey: Key added for user: `%s`', username)
    keys_file.close()

    # Explicitly setting read-only permissions to authorized_keys
    os.chmod(tmp_authorized_keys, stat.S_IRUSR | stat.S_IWUSR)
    # Rename is atomic operation
    os.rename(tmp_authorized_keys, authorized_keys_file_path)


def generate_ssh_authorized_keys_file(registry):
    log.info('Generating new authorized key file')

    authorized_keys_file_path = registry.settings.get(
        config_keys.authorized_keys_file_path)

    ssh_wrapper_cmd = registry.settings.get(
        config_keys.wrapper_cmd)
    allow_shell = registry.settings.get(
        config_keys.wrapper_allow_shell)
    ssh_opts = registry.settings.get(
        config_keys.authorized_keys_line_ssh_opts)
    debug = registry.settings.get(
        config_keys.enable_debug_logging)

    _generate_ssh_authorized_keys_file(
        authorized_keys_file_path, ssh_wrapper_cmd, allow_shell, ssh_opts,
        debug)

    return 0
