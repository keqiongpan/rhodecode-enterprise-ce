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


import logging

from pyramid.renderers import render

from rhodecode.model.db import RepoGroup
from rhodecode.svn_support import keys


log = logging.getLogger(__name__)


def generate_mod_dav_svn_config(event):
    """
    Subscriber to the `rhodcode.events.RepoGroupEvent`. This triggers the
    automatic generation of mod_dav_svn config file on repository group
    changes.
    """
    _generate(event.request.registry.settings)


def _generate(settings):
    """
    Generate the configuration file for use with subversion's mod_dav_svn
    module. The configuration has to contain a <Location> block for each
    available repository group because the mod_dav_svn module does not support
    repositories organized in sub folders.

    Currently this is only used by the subscriber above. If we extend this
    to include it as API method and in the web interface this should be moved
    to an appropriate place.
    """
    filepath = settings[keys.config_file_path]
    repository_root = settings[keys.parent_path_root]
    list_parent_path = settings[keys.list_parent_path]
    location_root = settings[keys.location_root]

    # Render the configuration to string.
    template = 'rhodecode:svn_support/templates/mod-dav-svn.conf.mako'
    context = {
        'location_root': location_root,
        'repository_root': repository_root,
        'repo_groups': RepoGroup.get_all_repo_groups(),
        'svn_list_parent_path': list_parent_path,
    }
    mod_dav_svn_config = render(template, context)

    # Write configuration to file.
    with open(filepath, 'w') as file_:
        file_.write(mod_dav_svn_config)
