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

import unicodedata


def strip_preparer(value):
    """
    strips given values using .strip() function
    """

    if value:
        value = value.strip()
    return value


def slugify_preparer(value, keep_case=True):
    """
    Slugify given value to a safe representation for url/id
    """
    from rhodecode.lib.utils import repo_name_slug
    if value:
        value = repo_name_slug(value if keep_case else value.lower())
    return value


def non_ascii_strip_preparer(value):
    """
    trie to replace non-ascii letters to their ascii representation
    eg::

        `żołw` converts into `zolw`
    """
    if value:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    return value


def unique_list_preparer(value):
    """
    Converts an list to a list with only unique values
    """

    def make_unique(value):
        seen = []
        return [c for c in value if
                not (c in seen or seen.append(c))]

    if isinstance(value, list):
        ret_val = make_unique(value)
    elif isinstance(value, set):
        ret_val = list(value)
    elif isinstance(value, tuple):
        ret_val = make_unique(value)
    elif value is None:
        ret_val = []
    else:
        ret_val = [value]

    return ret_val


def unique_list_from_str_preparer(value):
    """
    Converts an list to a list with only unique values
    """
    from rhodecode.lib.utils2 import aslist

    if isinstance(value, basestring):
        value = aslist(value, ',')
    return unique_list_preparer(value)