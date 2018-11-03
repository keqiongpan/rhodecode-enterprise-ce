# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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

from whoosh.qparser.default import QueryParser, query
from whoosh.qparser.dateparse import DateParserPlugin
from whoosh.fields import (TEXT, Schema, DATETIME)
from sqlalchemy.sql.expression import or_, and_, not_, func

from rhodecode.model.db import UserLog
from rhodecode.lib.utils2 import remove_prefix, remove_suffix, safe_unicode

# JOURNAL SCHEMA used only to generate queries in journal. We use whoosh
# querylang to build sql queries and filter journals
JOURNAL_SCHEMA = Schema(
    username=TEXT(),
    date=DATETIME(),
    action=TEXT(),
    repository=TEXT(),
    ip=TEXT(),
)

log = logging.getLogger(__name__)


def user_log_filter(user_log, search_term):
    """
    Filters sqlalchemy user_log based on search_term with whoosh Query language
    http://packages.python.org/Whoosh/querylang.html

    :param user_log:
    :param search_term:
    """
    log.debug('Initial search term: %r', search_term)
    qry = None
    if search_term:
        qp = QueryParser('repository', schema=JOURNAL_SCHEMA)
        qp.add_plugin(DateParserPlugin())
        qry = qp.parse(safe_unicode(search_term))
        log.debug('Filtering using parsed query %r', qry)

    def wildcard_handler(col, wc_term):
        if wc_term.startswith('*') and not wc_term.endswith('*'):
            # postfix == endswith
            wc_term = remove_prefix(wc_term, prefix='*')
            return func.lower(col).endswith(wc_term)
        elif wc_term.startswith('*') and wc_term.endswith('*'):
            # wildcard == ilike
            wc_term = remove_prefix(wc_term, prefix='*')
            wc_term = remove_suffix(wc_term, suffix='*')
            return func.lower(col).contains(wc_term)

    def get_filterion(field, val, term):

        if field == 'repository':
            field = getattr(UserLog, 'repository_name')
        elif field == 'ip':
            field = getattr(UserLog, 'user_ip')
        elif field == 'date':
            field = getattr(UserLog, 'action_date')
        elif field == 'username':
            field = getattr(UserLog, 'username')
        else:
            field = getattr(UserLog, field)
        log.debug('filter field: %s val=>%s', field, val)

        # sql filtering
        if isinstance(term, query.Wildcard):
            return wildcard_handler(field, val)
        elif isinstance(term, query.Prefix):
            return func.lower(field).startswith(func.lower(val))
        elif isinstance(term, query.DateRange):
            return and_(field >= val[0], field <= val[1])
        elif isinstance(term, query.Not):
            return not_(field == val)
        return func.lower(field) == func.lower(val)

    if isinstance(qry, (query.And, query.Not, query.Term, query.Prefix,
                        query.Wildcard, query.DateRange)):
        if not isinstance(qry, query.And):
            qry = [qry]

        for term in qry:
            if isinstance(term, query.Not):
                not_term = [z for z in term.leaves()][0]
                field = not_term.fieldname
                val = not_term.text
            elif isinstance(term, query.DateRange):
                field = term.fieldname
                val = [term.startdate, term.enddate]
            elif isinstance(term, query.NullQuery.__class__):
                field = ''
                val = ''
            else:
                field = term.fieldname
                val = term.text
            if field:
                user_log = user_log.filter(get_filterion(field, val, term))
    elif isinstance(qry, query.Or):
        filters = []
        for term in qry:
            field = term.fieldname
            val = (term.text if not isinstance(term, query.DateRange)
                   else [term.startdate, term.enddate])
            filters.append(get_filterion(field, val, term))
        user_log = user_log.filter(or_(*filters))

    return user_log
