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


# Definition of setting keys used to configure this module. Defined here to
# avoid repetition of keys throughout the module.
config_file_path = 'svn.proxy.config_file_path'
generate_config = 'svn.proxy.generate_config'
list_parent_path = 'svn.proxy.list_parent_path'
location_root = 'svn.proxy.location_root'
reload_command = 'svn.proxy.reload_cmd'
reload_timeout = 'svn.proxy.reload_timeout'
template = 'svn.proxy.config_template'
