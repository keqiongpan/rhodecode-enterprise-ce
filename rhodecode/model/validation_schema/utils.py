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

import deform.widget


def convert_to_optgroup(items):
    """
    Convert such format::

        [
            ['rev:tip', u'latest tip'], 
            ([(u'branch:default', u'default')], u'Branches'), 
        ]

    into one used by deform Select widget::

        (
            ('rev:tip', 'latest tip'),
            OptGroup('Branches',
                    ('branch:default', 'default'),
        )
    """
    result = []
    for value, label in items:
        # option group
        if isinstance(value, (tuple, list)):
            result.append(deform.widget.OptGroup(label, *value))
        else:
            result.append((value, label))

    return result


def username_converter(value):
    for noise in ('/', ',', '*', '"', "'", '<', '>', '(', ')', '[', ']', ';'):
        value = value.replace(noise, '')

    return value
