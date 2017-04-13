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

import time
import logging
from pylons import tmpl_context as c
from pyramid.httpexceptions import HTTPFound

from rhodecode.lib import helpers as h
from rhodecode.lib.utils2 import StrictAttributeDict, safe_int
from rhodecode.model import repo
from rhodecode.model.db import User
from rhodecode.model.scm import ScmModel

log = logging.getLogger(__name__)


ADMIN_PREFIX = '/_admin'
STATIC_FILE_PREFIX = '/_static'


class TemplateArgs(StrictAttributeDict):
    pass


class BaseAppView(object):

    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.session = request.session
        self._rhodecode_user = request.user  # auth user
        self._rhodecode_db_user = self._rhodecode_user.get_instance()
        self._maybe_needs_password_change(
            request.matched_route.name, self._rhodecode_db_user)

    def _maybe_needs_password_change(self, view_name, user_obj):
        log.debug('Checking if user %s needs password change on view %s',
                  user_obj, view_name)
        skip_user_views = [
            'logout', 'login',
            'my_account_password', 'my_account_password_update'
        ]

        if not user_obj:
            return

        if user_obj.username == User.DEFAULT_USER:
            return

        now = time.time()
        should_change = user_obj.user_data.get('force_password_change')
        change_after = safe_int(should_change) or 0
        if should_change and now > change_after:
            log.debug('User %s requires password change', user_obj)
            h.flash('You are required to change your password', 'warning',
                    ignore_duplicate=True)

            if view_name not in skip_user_views:
                raise HTTPFound(
                    self.request.route_path('my_account_password'))

    def _get_local_tmpl_context(self):
        c = TemplateArgs()
        c.auth_user = self.request.user
        return c

    def _register_global_c(self, tmpl_args):
        """
        Registers attributes to pylons global `c`
        """
        # TODO(marcink): remove once pyramid migration is finished
        for k, v in tmpl_args.items():
            setattr(c, k, v)

    def _get_template_context(self, tmpl_args):
        self._register_global_c(tmpl_args)

        local_tmpl_args = {
            'defaults': {},
            'errors': {},
        }
        local_tmpl_args.update(tmpl_args)
        return local_tmpl_args

    def load_default_context(self):
        """
        example:

        def load_default_context(self):
            c = self._get_local_tmpl_context()
            c.custom_var = 'foobar'
            self._register_global_c(c)
            return c
        """
        raise NotImplementedError('Needs implementation in view class')


class RepoAppView(BaseAppView):

    def __init__(self, context, request):
        super(RepoAppView, self).__init__(context, request)
        self.db_repo = request.db_repo
        self.db_repo_name = self.db_repo.repo_name
        self.db_repo_pull_requests = ScmModel().get_pull_requests(self.db_repo)

    def _get_local_tmpl_context(self):
        c = super(RepoAppView, self)._get_local_tmpl_context()
        # register common vars for this type of view
        c.rhodecode_db_repo = self.db_repo
        c.repo_name = self.db_repo_name
        c.repository_pull_requests = self.db_repo_pull_requests
        return c


class DataGridAppView(object):
    """
    Common class to have re-usable grid rendering components
    """

    def _extract_ordering(self, request):
        column_index = safe_int(request.GET.get('order[0][column]'))
        order_dir = request.GET.get(
            'order[0][dir]', 'desc')
        order_by = request.GET.get(
            'columns[%s][data][sort]' % column_index, 'name_raw')

        # translate datatable to DB columns
        order_by = {
            'first_name': 'name',
            'last_name': 'lastname',
        }.get(order_by) or order_by

        search_q = request.GET.get('search[value]')
        return search_q, order_by, order_dir

    def _extract_chunk(self, request):
        start = safe_int(request.GET.get('start'), 0)
        length = safe_int(request.GET.get('length'), 25)
        draw = safe_int(request.GET.get('draw'))
        return draw, start, length


class RepoRoutePredicate(object):
    def __init__(self, val, config):
        self.val = val

    def text(self):
        return 'repo_route = %s' % self.val

    phash = text

    def __call__(self, info, request):
        repo_name = info['match']['repo_name']
        repo_model = repo.RepoModel()
        by_name_match = repo_model.get_by_repo_name(repo_name, cache=True)
        # if we match quickly from database, short circuit the operation,
        # and validate repo based on the type.
        if by_name_match:
            # register this as request object we can re-use later
            request.db_repo = by_name_match
            return True

        by_id_match = repo_model.get_repo_by_id(repo_name)
        if by_id_match:
            request.db_repo = by_id_match
            return True

        return False


def includeme(config):
    config.add_route_predicate(
        'repo_route', RepoRoutePredicate)
