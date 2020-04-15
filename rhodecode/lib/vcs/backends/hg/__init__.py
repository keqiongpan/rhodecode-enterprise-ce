# -*- coding: utf-8 -*-

# Copyright (C) 2014-2020 RhodeCode GmbH
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

"""
HG module
"""
import os
import logging

from rhodecode.lib.vcs import connection
from rhodecode.lib.vcs.backends.hg.commit import MercurialCommit
from rhodecode.lib.vcs.backends.hg.inmemory import MercurialInMemoryCommit
from rhodecode.lib.vcs.backends.hg.repository import MercurialRepository


log = logging.getLogger(__name__)


def discover_hg_version(raise_on_exc=False):
    """
    Returns the string as it was returned by running 'git --version'

    It will return an empty string in case the connection is not initialized
    or no vcsserver is available.
    """
    try:
        return connection.Hg.discover_hg_version()
    except Exception:
        log.warning("Failed to discover the HG version", exc_info=True)
        if raise_on_exc:
            raise
        return ''


def largefiles_store(base_location):
    """
    Return a largefile store relative to base_location
    """
    return os.path.join(base_location, '.cache', 'largefiles')
