# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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
from rhodecode.apps.file_store import config_keys
from rhodecode.config.middleware import _bool_setting, _string_setting


def _sanitize_settings_and_apply_defaults(settings):
    """
    Set defaults, convert to python types and validate settings.
    """
    _bool_setting(settings, config_keys.enabled, 'true')

    _string_setting(settings, config_keys.backend, 'local')

    default_store = os.path.join(os.path.dirname(settings['__file__']), 'upload_store')
    _string_setting(settings, config_keys.store_path, default_store)


def includeme(config):
    settings = config.registry.settings
    _sanitize_settings_and_apply_defaults(settings)

    config.add_route(
        name='upload_file',
        pattern='/_file_store/upload')
    config.add_route(
        name='download_file',
        pattern='/_file_store/download/{fid}')
    config.add_route(
        name='download_file_by_token',
        pattern='/_file_store/token-download/{_auth_token}/{fid}')

    # Scan module for configuration decorators.
    config.scan('.views', ignore='.tests')
