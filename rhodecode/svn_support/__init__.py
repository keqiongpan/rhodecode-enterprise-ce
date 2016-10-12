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
from rhodecode.config.middleware import _bool_setting, _string_setting

from .subscribers import generate_config_subscriber
from . import config_keys


log = logging.getLogger(__name__)


def includeme(config):
    settings = config.registry.settings
    _sanitize_settings_and_apply_defaults(settings)

    if settings[config_keys.generate_config]:
        config.add_subscriber(
            generate_config_subscriber, events.RepoGroupEvent)


def _sanitize_settings_and_apply_defaults(settings):
    """
    Set defaults, convert to python types and validate settings.
    """
    # Convert bool settings from string to bool.
    _bool_setting(settings, config_keys.generate_config, 'false')
    _bool_setting(settings, config_keys.list_parent_path, 'true')
    _string_setting(settings, config_keys.config_file_path, '', lower=False)
    _string_setting(settings, config_keys.location_root, '/', lower=False)
    _string_setting(settings, config_keys.reload_command, '', lower=False)

    # Append path separator to location root.
    settings[config_keys.location_root] = _append_path_sep(
        settings[config_keys.location_root])

    # Validate settings.
    if settings[config_keys.generate_config]:
        assert len(settings[config_keys.config_file_path]) > 0


def _append_path_sep(path):
    """
    Append the path separator if missing.
    """
    if isinstance(path, basestring) and not path.endswith(os.path.sep):
        path += os.path.sep
    return path
