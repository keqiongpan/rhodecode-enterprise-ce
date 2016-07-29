# -*- coding: utf-8 -*-

# Copyright (C) 2016-2016  RhodeCode GmbH
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

from pyramid.renderers import render

from rhodecode.model.db import RepoGroup
from . import config_keys


def generate_mod_dav_svn_config(settings):
    """
    Generate the configuration file for use with subversion's mod_dav_svn
    module. The configuration has to contain a <Location> block for each
    available repository group because the mod_dav_svn module does not support
    repositories organized in sub folders.
    """
    filepath = settings[config_keys.config_file_path]
    parent_path_root = settings[config_keys.parent_path_root]
    list_parent_path = settings[config_keys.list_parent_path]
    location_root = settings[config_keys.location_root]

    # Render the configuration to string.
    template = 'rhodecode:svn_support/templates/mod-dav-svn.conf.mako'
    context = {
        'location_root': location_root,
        'location_root_stripped': location_root.rstrip(os.path.sep),
        'parent_path_root': parent_path_root,
        'parent_path_root_stripped': parent_path_root.rstrip(os.path.sep),
        'repo_groups': RepoGroup.get_all_repo_groups(),
        'svn_list_parent_path': list_parent_path,
    }
    mod_dav_svn_config = render(template, context)

    # Write configuration to file.
    with open(filepath, 'w') as file_:
        file_.write(mod_dav_svn_config)
