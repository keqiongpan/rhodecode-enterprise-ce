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

import pickle
import pytest

from rhodecode.lib.jsonalchemy import MutationDict, MutationList


def test_mutation_dict_is_picklable():
    mutation_dict = MutationDict({'key1': 'value1', 'key2': 'value2'})
    dumped = pickle.dumps(mutation_dict)
    loaded = pickle.loads(dumped)
    assert loaded == mutation_dict

def test_mutation_list_is_picklable():
    mutation_list = MutationList(['a', 'b', 'c'])
    dumped = pickle.dumps(mutation_list)
    loaded = pickle.loads(dumped)
    assert loaded == mutation_list

def test_mutation_dict_with_lists_is_picklable():
    mutation_dict = MutationDict({
        'key': MutationList(['values', MutationDict({'key': 'value'})])
    })
    dumped = pickle.dumps(mutation_dict)
    loaded = pickle.loads(dumped)
    assert loaded == mutation_dict
