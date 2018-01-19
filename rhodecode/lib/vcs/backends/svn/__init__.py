# -*- coding: utf-8 -*-

# Copyright (C) 2014-2018 RhodeCode GmbH
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
SVN module
"""
import logging

from rhodecode.lib.vcs import connection
from rhodecode.lib.vcs.backends.svn.commit import SubversionCommit
from rhodecode.lib.vcs.backends.svn.repository import SubversionRepository


log = logging.getLogger(__name__)


def discover_svn_version(raise_on_exc=False):
    """
    Returns the string as it was returned by running 'git --version'

    It will return an empty string in case the connection is not initialized
    or no vcsserver is available.
    """
    try:
        return connection.Svn.discover_svn_version()
    except Exception:
        log.warning("Failed to discover the SVN version", exc_info=True)
        if raise_on_exc:
            raise
        return ''
