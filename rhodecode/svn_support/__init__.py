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
import os

from rhodecode import events
from rhodecode.lib.utils2 import str2bool
from rhodecode.svn_support.subscribers import generate_mod_dav_svn_config
from rhodecode.svn_support import keys


log = logging.getLogger(__name__)


def includeme(config):
    settings = config.registry.settings
    _sanitize_settings_and_apply_defaults(settings)

    if settings[keys.generate_config]:
        log.error('Add subscriber')
        config.add_subscriber(
            generate_mod_dav_svn_config, events.RepoGroupEvent)


def _sanitize_settings_and_apply_defaults(settings):
    # Convert bool settings from string to bool.
    settings[keys.generate_config] = str2bool(
        settings.get(keys.generate_config, 'false'))
    settings[keys.list_parent_path] = str2bool(
        settings.get(keys.list_parent_path, 'true'))

    # Set defaults if key not present.
    settings.setdefault(keys.config_file_path, None)
    settings.setdefault(keys.location_root, '/')
    settings.setdefault(keys.parent_path_root, None)

    # Append path separator to paths.
    settings[keys.location_root] = _append_slash(
        settings[keys.location_root])
    settings[keys.parent_path_root] = _append_slash(
        settings[keys.parent_path_root])

    # Validate settings.
    if settings[keys.generate_config]:
        assert settings[keys.config_file_path] is not None


def _append_slash(path):
    if isinstance(path, basestring) and not path.endswith(os.path.sep):
        path += os.path.sep
    return path
