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


# Definition of setting keys used to configure this module. Defined here to
# avoid repetition of keys throughout the module.
generate_authorized_keyfile = 'ssh.generate_authorized_keyfile'
authorized_keys_file_path = 'ssh.authorized_keys_file_path'
authorized_keys_line_ssh_opts = 'ssh.authorized_keys_ssh_opts'
wrapper_cmd = 'ssh.wrapper_cmd'
wrapper_allow_shell = 'ssh.wrapper_cmd_allow_shell'
enable_debug_logging = 'ssh.enable_debug_logging'

ssh_hg_bin = 'ssh.executable.hg'
ssh_git_bin = 'ssh.executable.git'
ssh_svn_bin = 'ssh.executable.svn'
