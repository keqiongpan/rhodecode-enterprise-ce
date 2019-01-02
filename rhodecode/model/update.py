# -*- coding: utf-8 -*-

# Copyright (C) 2013-2019 RhodeCode GmbH
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
import urllib2
from packaging.version import Version

import rhodecode
from rhodecode.lib.ext_json import json
from rhodecode.model import BaseModel
from rhodecode.model.meta import Session
from rhodecode.model.settings import SettingsModel


log = logging.getLogger(__name__)


class UpdateModel(BaseModel):
    UPDATE_SETTINGS_KEY = 'update_version'
    UPDATE_URL_SETTINGS_KEY = 'rhodecode_update_url'

    @staticmethod
    def get_update_data(update_url):
        """Return the JSON update data."""
        ver = rhodecode.__version__
        log.debug('Checking for upgrade on `%s` server', update_url)
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'RhodeCode-SCM/%s' % ver)]
        response = opener.open(update_url)
        response_data = response.read()
        data = json.loads(response_data)
        log.debug('update server returned data')
        return data

    def get_update_url(self):
        settings = SettingsModel().get_all_settings()
        return settings.get(self.UPDATE_URL_SETTINGS_KEY)

    def store_version(self, version):
        log.debug('Storing version %s into settings', version)
        setting = SettingsModel().create_or_update_setting(
            self.UPDATE_SETTINGS_KEY, version)
        Session().add(setting)
        Session().commit()

    def get_stored_version(self):
        obj = SettingsModel().get_setting_by_name(self.UPDATE_SETTINGS_KEY)
        if obj:
            return obj.app_settings_value
        return '0.0.0'

    def _sanitize_version(self, version):
        """
        Cleanup our custom ver.
        e.g 4.11.0_20171204_204825_CE_default_EE_default to 4.11.0
        """
        return version.split('_')[0]

    def is_outdated(self, cur_version, latest_version=None):
        latest_version = latest_version or self.get_stored_version()
        try:
            cur_version = self._sanitize_version(cur_version)
            return Version(latest_version) > Version(cur_version)
        except Exception:
            # could be invalid version, etc
            return False
