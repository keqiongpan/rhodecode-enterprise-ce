# -*- coding: utf-8 -*-

# Copyright (C) 2013-2017 RhodeCode GmbH
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
my account controller for RhodeCode admin
"""

import logging

import formencode
from formencode import htmlfill
from pyramid.httpexceptions import HTTPFound

from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n.translation import _

from rhodecode.lib import helpers as h
from rhodecode.lib import auth
from rhodecode.lib.auth import (
    LoginRequired, NotAnonymous, AuthUser)
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.utils2 import safe_int, str2bool
from rhodecode.lib.ext_json import json

from rhodecode.model.db import (
    Repository, PullRequest, UserEmailMap, User, UserFollowing)
from rhodecode.model.forms import UserForm
from rhodecode.model.user import UserModel
from rhodecode.model.meta import Session
from rhodecode.model.pull_request import PullRequestModel
from rhodecode.model.comment import CommentsModel

log = logging.getLogger(__name__)


class MyAccountController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('setting', 'settings', controller='admin/settings',
    #         path_prefix='/admin', name_prefix='admin_')

    @LoginRequired()
    @NotAnonymous()
    def __before__(self):
        super(MyAccountController, self).__before__()

    def __load_data(self):
        c.user = User.get(c.rhodecode_user.user_id)
        if c.user.username == User.DEFAULT_USER:
            h.flash(_("You can't edit this user since it's"
                      " crucial for entire application"), category='warning')
            return redirect(h.route_path('users'))

        c.auth_user = AuthUser(
            user_id=c.rhodecode_user.user_id, ip_addr=self.ip_addr)

    @auth.CSRFRequired()
    def my_account_update(self):
        """
        POST /_admin/my_account Updates info of my account
        """
        # url('my_account')
        c.active = 'profile_edit'
        self.__load_data()
        c.perm_user = c.auth_user
        c.extern_type = c.user.extern_type
        c.extern_name = c.user.extern_name

        defaults = c.user.get_dict()
        update = False
        _form = UserForm(edit=True,
                         old_data={'user_id': c.rhodecode_user.user_id,
                                   'email': c.rhodecode_user.email})()
        form_result = {}
        try:
            post_data = dict(request.POST)
            post_data['new_password'] = ''
            post_data['password_confirmation'] = ''
            form_result = _form.to_python(post_data)
            # skip updating those attrs for my account
            skip_attrs = ['admin', 'active', 'extern_type', 'extern_name',
                          'new_password', 'password_confirmation']
            # TODO: plugin should define if username can be updated
            if c.extern_type != "rhodecode":
                # forbid updating username for external accounts
                skip_attrs.append('username')

            UserModel().update_user(
                c.rhodecode_user.user_id, skip_attrs=skip_attrs, **form_result)
            h.flash(_('Your account was updated successfully'),
                    category='success')
            Session().commit()
            update = True

        except formencode.Invalid as errors:
            return htmlfill.render(
                render('admin/my_account/my_account.mako'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False)
        except Exception:
            log.exception("Exception updating user")
            h.flash(_('Error occurred during update of user %s')
                    % form_result.get('username'), category='error')

        if update:
            raise HTTPFound(h.route_path('my_account_profile'))

        return htmlfill.render(
            render('admin/my_account/my_account.mako'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )

    def my_account_edit(self):
        """
        GET /_admin/my_account/edit Displays edit form of my account
        """
        c.active = 'profile_edit'
        self.__load_data()
        c.perm_user = c.auth_user
        c.extern_type = c.user.extern_type
        c.extern_name = c.user.extern_name

        defaults = c.user.get_dict()
        return htmlfill.render(
            render('admin/my_account/my_account.mako'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )

    def _extract_ordering(self, request):
        column_index = safe_int(request.GET.get('order[0][column]'))
        order_dir = request.GET.get('order[0][dir]', 'desc')
        order_by = request.GET.get(
            'columns[%s][data][sort]' % column_index, 'name_raw')
        return order_by, order_dir

    def _get_pull_requests_list(self, statuses):
        start = safe_int(request.GET.get('start'), 0)
        length = safe_int(request.GET.get('length'), c.visual.dashboard_items)
        order_by, order_dir = self._extract_ordering(request)

        pull_requests = PullRequestModel().get_im_participating_in(
            user_id=c.rhodecode_user.user_id,
            statuses=statuses,
            offset=start, length=length, order_by=order_by,
            order_dir=order_dir)

        pull_requests_total_count = PullRequestModel().count_im_participating_in(
            user_id=c.rhodecode_user.user_id, statuses=statuses)

        from rhodecode.lib.utils import PartialRenderer
        _render = PartialRenderer('data_table/_dt_elements.mako')
        data = []
        for pr in pull_requests:
            repo_id = pr.target_repo_id
            comments = CommentsModel().get_all_comments(
                repo_id, pull_request=pr)
            owned = pr.user_id == c.rhodecode_user.user_id
            status = pr.calculated_review_status()

            data.append({
                'target_repo': _render('pullrequest_target_repo',
                                       pr.target_repo.repo_name),
                'name': _render('pullrequest_name',
                                pr.pull_request_id, pr.target_repo.repo_name,
                                short=True),
                'name_raw': pr.pull_request_id,
                'status': _render('pullrequest_status', status),
                'title': _render(
                    'pullrequest_title', pr.title, pr.description),
                'description': h.escape(pr.description),
                'updated_on': _render('pullrequest_updated_on',
                                      h.datetime_to_time(pr.updated_on)),
                'updated_on_raw': h.datetime_to_time(pr.updated_on),
                'created_on': _render('pullrequest_updated_on',
                                      h.datetime_to_time(pr.created_on)),
                'created_on_raw': h.datetime_to_time(pr.created_on),
                'author': _render('pullrequest_author',
                                  pr.author.full_contact, ),
                'author_raw': pr.author.full_name,
                'comments': _render('pullrequest_comments', len(comments)),
                'comments_raw': len(comments),
                'closed': pr.is_closed(),
                'owned': owned
            })
        # json used to render the grid
        data = ({
            'data': data,
            'recordsTotal': pull_requests_total_count,
            'recordsFiltered': pull_requests_total_count,
        })
        return data

    def my_account_pullrequests(self):
        c.active = 'pullrequests'
        self.__load_data()
        c.show_closed = str2bool(request.GET.get('pr_show_closed'))

        statuses = [PullRequest.STATUS_NEW, PullRequest.STATUS_OPEN]
        if c.show_closed:
            statuses += [PullRequest.STATUS_CLOSED]
        data = self._get_pull_requests_list(statuses)
        if not request.is_xhr:
            c.data_participate = json.dumps(data['data'])
            c.records_total_participate = data['recordsTotal']
            return render('admin/my_account/my_account.mako')
        else:
            return json.dumps(data)


