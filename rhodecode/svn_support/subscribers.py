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


from .utils import generate_mod_dav_svn_config


log = logging.getLogger(__name__)


def generate_config_subscriber(event):
    """
    Subscriber to the `rhodcode.events.RepoGroupEvent`. This triggers the
    automatic generation of mod_dav_svn config file on repository group
    changes.
    """
    try:
        generate_mod_dav_svn_config(event.request.registry)
    except Exception:
        log.exception(
            'Exception while generating subversion mod_dav_svn configuration.')
