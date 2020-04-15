# -*- coding: utf-8 -*-

# Copyright (C) 2012-2020 RhodeCode GmbH
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
Index schema for RhodeCode
"""

import importlib
import logging

from rhodecode.lib.index.search_utils import normalize_text_for_matching

log = logging.getLogger(__name__)

# leave defaults for backward compat
default_searcher = 'rhodecode.lib.index.whoosh'
default_location = '%(here)s/data/index'

ES_VERSION_2 = '2'
ES_VERSION_6 = '6'
# for legacy reasons we keep 2 compat as default
DEFAULT_ES_VERSION = ES_VERSION_2

from rhodecode_tools.lib.fts_index.elasticsearch_engine_6 import \
    ES_CONFIG  # pragma: no cover


class BaseSearcher(object):
    query_lang_doc = ''
    es_version = None
    name = None
    DIRECTION_ASC = 'asc'
    DIRECTION_DESC = 'desc'

    def __init__(self):
        pass

    def cleanup(self):
        pass

    def search(self, query, document_type, search_user,
               repo_name=None, repo_group_name=None,
               raise_on_exc=True):
        raise Exception('NotImplemented')

    @staticmethod
    def query_to_mark(query, default_field=None):
        """
        Formats the query to mark token for jquery.mark.js highlighting. ES could
        have a different format optionally.

        :param default_field:
        :param query:
        """
        return ' '.join(normalize_text_for_matching(query).split())

    @property
    def is_es_6(self):
        return self.es_version == ES_VERSION_6

    def get_handlers(self):
        return {}

    @staticmethod
    def extract_search_tags(query):
        return []

    @staticmethod
    def escape_specials(val):
        """
        Handle and escape reserved chars for search
        """
        return val

    def sort_def(self, search_type, direction, sort_field):
        """
        Defines sorting for search. This function should decide if for given
        search_type, sorting can be done with sort_field.

        It also should translate common sort fields into backend specific. e.g elasticsearch
        """
        raise NotImplementedError()

    @staticmethod
    def get_sort(search_type, search_val):
        """
        Method used to parse the GET search sort value to a field and direction.
        e.g asc:lines == asc, lines

        There's also a legacy support for newfirst/oldfirst which defines commit
        sorting only
        """

        direction = BaseSearcher.DIRECTION_ASC
        sort_field = None

        if not search_val:
            return direction, sort_field

        if search_val.startswith('asc:'):
            sort_field = search_val[4:]
            direction = BaseSearcher.DIRECTION_ASC
        elif search_val.startswith('desc:'):
            sort_field = search_val[5:]
            direction = BaseSearcher.DIRECTION_DESC
        elif search_val == 'newfirst' and search_type == 'commit':
            sort_field = 'date'
            direction = BaseSearcher.DIRECTION_DESC
        elif search_val == 'oldfirst' and search_type == 'commit':
            sort_field = 'date'
            direction = BaseSearcher.DIRECTION_ASC

        return direction, sort_field


def search_config(config, prefix='search.'):
    _config = {}
    for key in config.keys():
        if key.startswith(prefix):
            _config[key[len(prefix):]] = config[key]
    return _config


def searcher_from_config(config, prefix='search.'):
    _config = search_config(config, prefix)

    if 'location' not in _config:
        _config['location'] = default_location
    if 'es_version' not in _config:
        # use old legacy ES version set to 2
        _config['es_version'] = '2'

    imported = importlib.import_module(_config.get('module', default_searcher))
    searcher = imported.Searcher(config=_config)
    return searcher
