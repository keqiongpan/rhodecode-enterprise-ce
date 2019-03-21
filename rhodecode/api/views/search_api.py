# -*- coding: utf-8 -*-

# Copyright (C) 2011-2018 RhodeCode GmbH
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

from rhodecode.api import jsonrpc_method
from rhodecode.api.exc import JSONRPCValidationError
from rhodecode.api.utils import Optional
from rhodecode.lib.index import searcher_from_config
from rhodecode.model import validation_schema
from rhodecode.model.validation_schema.schemas import search_schema

log = logging.getLogger(__name__)


@jsonrpc_method()
def search(request, apiuser, search_query, search_type, page_limit=Optional(10), page=Optional(1), search_sort=Optional('newfirst'), repo_name=Optional(None)):
    """
    Search

    :param apiuser: This is filled automatically from the |authtoken|.
    :type apiuser: AuthUser
    :param search_query: Search query.
    :type search_query: str
    :param search_type: Search type. either commit or content.
    :type search_type: str
    :param page_limit: Page item limit. Default 10 items.
    :type page_limit: Optional(int)
    :param page: Page number. Default first page.
    :type page: Optional(int)
    :param search_sort: Search sort. Default newfirst.
    :type search_sort: Optional(str)
    :param repo_name: Filter by one repo. Default is all.
    :type repo_name: Optional(str)
    """

    searcher = searcher_from_config(request.registry.settings)
    data = {'execution_time': ''}
    repo_name = Optional.extract(repo_name)

    schema = search_schema.SearchParamsSchema()

    search_params = {}
    try:
        search_params = schema.deserialize(
            dict(search_query=search_query,
                 search_type=search_type,
                 search_sort=Optional.extract(search_sort),
                 page_limit=Optional.extract(page_limit),
                 requested_page=Optional.extract(page))
        )
    except validation_schema.Invalid as err:
        raise JSONRPCValidationError(colander_exc=err)

    search_query = search_params.get('search_query')
    search_type = search_params.get('search_type')
    search_sort = search_params.get('search_sort')

    if search_params.get('search_query'):
        page_limit = search_params['page_limit']
        requested_page = search_params['requested_page']

        try:
            search_result = searcher.search(
                search_query, search_type, apiuser, repo_name,
                requested_page, page_limit, search_sort)

            data.update(dict(
                results=list(search_result['results']), page=requested_page,
                item_count=search_result['count'],
                items_per_page=page_limit))
        finally:
            searcher.cleanup()

        if not search_result['error']:
            data['execution_time'] = '%s results (%.3f seconds)' % (
                search_result['count'],
                search_result['runtime'])
        else:
            node = schema['search_query']
            raise JSONRPCValidationError(colander_exc=validation_schema.Invalid(node, search_result['error']))

    return data
