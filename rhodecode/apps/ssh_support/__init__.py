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

import logging

from . import config_keys
from .events import SshKeyFileChangeEvent
from .subscribers import generate_ssh_authorized_keys_file_subscriber

from rhodecode.config.middleware import _bool_setting, _string_setting

log = logging.getLogger(__name__)


def _sanitize_settings_and_apply_defaults(settings):
    """
    Set defaults, convert to python types and validate settings.
    """
    _bool_setting(settings, config_keys.generate_authorized_keyfile, 'false')
    _bool_setting(settings, config_keys.wrapper_allow_shell, 'false')
    _bool_setting(settings, config_keys.enable_debug_logging, 'false')

    _string_setting(settings, config_keys.authorized_keys_file_path,
                    '~/.ssh/authorized_keys_rhodecode',
                    lower=False)
    _string_setting(settings, config_keys.wrapper_cmd, '',
                    lower=False)
    _string_setting(settings, config_keys.authorized_keys_line_ssh_opts, '',
                    lower=False)

    _string_setting(settings, config_keys.ssh_hg_bin,
                    '~/.rccontrol/vcsserver-1/profile/bin/hg',
                    lower=False)
    _string_setting(settings, config_keys.ssh_git_bin,
                    '~/.rccontrol/vcsserver-1/profile/bin/git',
                    lower=False)
    _string_setting(settings, config_keys.ssh_svn_bin,
                    '~/.rccontrol/vcsserver-1/profile/bin/svnserve',
                    lower=False)


def includeme(config):
    settings = config.registry.settings
    _sanitize_settings_and_apply_defaults(settings)

    # if we have enable generation of file, subscribe to event
    if settings[config_keys.generate_authorized_keyfile]:
        config.add_subscriber(
            generate_ssh_authorized_keys_file_subscriber, SshKeyFileChangeEvent)
