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
import datetime
import logging
import time

import formencode
import formencode.htmlfill

from pyramid.httpexceptions import HTTPFound, HTTPForbidden

from pyramid.renderers import render
from pyramid.response import Response

from rhodecode import events
from rhodecode.apps._base import BaseAppView, DataGridAppView

from rhodecode.lib.auth import (
    LoginRequired, CSRFRequired, NotAnonymous,
    HasPermissionAny, HasRepoGroupPermissionAny)
from rhodecode.lib import helpers as h, audit_logger
from rhodecode.lib.utils2 import safe_int, safe_unicode, datetime_to_time
from rhodecode.model.forms import RepoGroupForm
from rhodecode.model.permission import PermissionModel
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.scm import RepoGroupList
from rhodecode.model.db import (
    or_, count, func, in_filter_generator, Session, RepoGroup, User, Repository)

log = logging.getLogger(__name__)


class AdminRepoGroupsView(BaseAppView, DataGridAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()

        return c

    def _load_form_data(self, c):
        allow_empty_group = False

        if self._can_create_repo_group():
            # we're global admin, we're ok and we can create TOP level groups
            allow_empty_group = True

        # override the choices for this form, we need to filter choices
        # and display only those we have ADMIN right
        groups_with_admin_rights = RepoGroupList(
            RepoGroup.query().all(),
            perm_set=['group.admin'], extra_kwargs=dict(user=self._rhodecode_user))
        c.repo_groups = RepoGroup.groups_choices(
            groups=groups_with_admin_rights,
            show_empty_group=allow_empty_group)
        c.personal_repo_group = self._rhodecode_user.personal_repo_group

    def _can_create_repo_group(self, parent_group_id=None):
        is_admin = HasPermissionAny('hg.admin')('group create controller')
        create_repo_group = HasPermissionAny(
            'hg.repogroup.create.true')('group create controller')
        if is_admin or (create_repo_group and not parent_group_id):
            # we're global admin, or we have global repo group create
            # permission
            # we're ok and we can create TOP level groups
            return True
        elif parent_group_id:
            # we check the permission if we can write to parent group
            group = RepoGroup.get(parent_group_id)
            group_name = group.group_name if group else None
            if HasRepoGroupPermissionAny('group.admin')(
                    group_name, 'check if user is an admin of group'):
                # we're an admin of passed in group, we're ok.
                return True
            else:
                return False
        return False

    # permission check in data loading of
    # `repo_group_list_data` via RepoGroupList
    @LoginRequired()
    @NotAnonymous()
    def repo_group_list(self):
        c = self.load_default_context()
        return self._get_template_context(c)

    # permission check inside
    @LoginRequired()
    @NotAnonymous()
    def repo_group_list_data(self):
        self.load_default_context()
        column_map = {
            'name': 'group_name_hash',
            'desc': 'group_description',
            'last_change': 'updated_on',
            'top_level_repos': 'repos_total',
            'owner': 'user_username',
        }
        draw, start, limit = self._extract_chunk(self.request)
        search_q, order_by, order_dir = self._extract_ordering(
            self.request, column_map=column_map)

        _render = self.request.get_partial_renderer(
            'rhodecode:templates/data_table/_dt_elements.mako')
        c = _render.get_call_context()

        def quick_menu(repo_group_name):
            return _render('quick_repo_group_menu', repo_group_name)

        def repo_group_lnk(repo_group_name):
            return _render('repo_group_name', repo_group_name)

        def last_change(last_change):
            if isinstance(last_change, datetime.datetime) and not last_change.tzinfo:
                ts = time.time()
                utc_offset = (datetime.datetime.fromtimestamp(ts)
                              - datetime.datetime.utcfromtimestamp(ts)).total_seconds()
                last_change = last_change + datetime.timedelta(seconds=utc_offset)
            return _render("last_change", last_change)

        def desc(desc, personal):
            return _render(
                'repo_group_desc', desc, personal, c.visual.stylify_metatags)

        def repo_group_actions(repo_group_id, repo_group_name, gr_count):
            return _render(
                'repo_group_actions', repo_group_id, repo_group_name, gr_count)

        def user_profile(username):
            return _render('user_profile', username)

        _perms = ['group.admin']
        allowed_ids = [-1] + self._rhodecode_user.repo_group_acl_ids_from_stack(_perms)

        repo_groups_data_total_count = RepoGroup.query()\
            .filter(or_(
                # generate multiple IN to fix limitation problems
                *in_filter_generator(RepoGroup.group_id, allowed_ids)
            )) \
            .count()

        repo_groups_data_total_inactive_count = RepoGroup.query()\
            .filter(RepoGroup.group_id.in_(allowed_ids))\
            .count()

        repo_count = count(Repository.repo_id)
        base_q = Session.query(
            RepoGroup.group_name,
            RepoGroup.group_name_hash,
            RepoGroup.group_description,
            RepoGroup.group_id,
            RepoGroup.personal,
            RepoGroup.updated_on,
            User,
            repo_count.label('repos_count')
            ) \
            .filter(or_(
                # generate multiple IN to fix limitation problems
                *in_filter_generator(RepoGroup.group_id, allowed_ids)
            )) \
            .outerjoin(Repository,  Repository.group_id == RepoGroup.group_id) \
            .join(User, User.user_id == RepoGroup.user_id) \
            .group_by(RepoGroup, User)

        if search_q:
            like_expression = u'%{}%'.format(safe_unicode(search_q))
            base_q = base_q.filter(or_(
                RepoGroup.group_name.ilike(like_expression),
            ))

        repo_groups_data_total_filtered_count = base_q.count()
        # the inactive isn't really used, but we still make it same as other data grids
        # which use inactive (users,user groups)
        repo_groups_data_total_filtered_inactive_count = repo_groups_data_total_filtered_count

        sort_defined = False
        if order_by == 'group_name':
            sort_col = func.lower(RepoGroup.group_name)
            sort_defined = True
        elif order_by == 'repos_total':
            sort_col = repo_count
            sort_defined = True
        elif order_by == 'user_username':
            sort_col = User.username
        else:
            sort_col = getattr(RepoGroup, order_by, None)

        if sort_defined or sort_col:
            if order_dir == 'asc':
                sort_col = sort_col.asc()
            else:
                sort_col = sort_col.desc()

        base_q = base_q.order_by(sort_col)
        base_q = base_q.offset(start).limit(limit)

        # authenticated access to user groups
        auth_repo_group_list = base_q.all()

        repo_groups_data = []
        for repo_gr in auth_repo_group_list:
            row = {
                "menu": quick_menu(repo_gr.group_name),
                "name": repo_group_lnk(repo_gr.group_name),

                "last_change": last_change(repo_gr.updated_on),

                "last_changeset": "",
                "last_changeset_raw": "",

                "desc": desc(repo_gr.group_description, repo_gr.personal),
                "owner": user_profile(repo_gr.User.username),
                "top_level_repos": repo_gr.repos_count,
                "action": repo_group_actions(
                    repo_gr.group_id, repo_gr.group_name, repo_gr.repos_count),

            }

            repo_groups_data.append(row)

        data = ({
            'draw': draw,
            'data': repo_groups_data,
            'recordsTotal': repo_groups_data_total_count,
            'recordsTotalInactive': repo_groups_data_total_inactive_count,
            'recordsFiltered': repo_groups_data_total_filtered_count,
            'recordsFilteredInactive': repo_groups_data_total_filtered_inactive_count,
        })

        return data

    @LoginRequired()
    @NotAnonymous()
    # perm checks inside
    def repo_group_new(self):
        c = self.load_default_context()

        # perm check for admin, create_group perm or admin of parent_group
        parent_group_id = safe_int(self.request.GET.get('parent_group'))
        _gr = RepoGroup.get(parent_group_id)
        if not self._can_create_repo_group(parent_group_id):
            raise HTTPForbidden()

        self._load_form_data(c)

        defaults = {}  # Future proof for default of repo group

        parent_group_choice = '-1'
        if not self._rhodecode_user.is_admin and self._rhodecode_user.personal_repo_group:
            parent_group_choice = self._rhodecode_user.personal_repo_group

        if parent_group_id and _gr:
            if parent_group_id in [x[0] for x in c.repo_groups]:
                parent_group_choice = safe_unicode(parent_group_id)

        defaults.update({'group_parent_id': parent_group_choice})

        data = render(
            'rhodecode:templates/admin/repo_groups/repo_group_add.mako',
            self._get_template_context(c), self.request)

        html = formencode.htmlfill.render(
            data,
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @NotAnonymous()
    @CSRFRequired()
    # perm checks inside
    def repo_group_create(self):
        c = self.load_default_context()
        _ = self.request.translate

        parent_group_id = safe_int(self.request.POST.get('group_parent_id'))
        can_create = self._can_create_repo_group(parent_group_id)

        self._load_form_data(c)
        # permissions for can create group based on parent_id are checked
        # here in the Form
        available_groups = map(lambda k: safe_unicode(k[0]), c.repo_groups)
        repo_group_form = RepoGroupForm(
            self.request.translate, available_groups=available_groups,
            can_create_in_root=can_create)()

        repo_group_name = self.request.POST.get('group_name')
        try:
            owner = self._rhodecode_user
            form_result = repo_group_form.to_python(dict(self.request.POST))
            copy_permissions = form_result.get('group_copy_permissions')
            repo_group = RepoGroupModel().create(
                group_name=form_result['group_name_full'],
                group_description=form_result['group_description'],
                owner=owner.user_id,
                copy_permissions=form_result['group_copy_permissions']
            )
            Session().flush()

            repo_group_data = repo_group.get_api_data()
            audit_logger.store_web(
                'repo_group.create', action_data={'data': repo_group_data},
                user=self._rhodecode_user)

            Session().commit()

            _new_group_name = form_result['group_name_full']

            repo_group_url = h.link_to(
                _new_group_name,
                h.route_path('repo_group_home', repo_group_name=_new_group_name))
            h.flash(h.literal(_('Created repository group %s')
                    % repo_group_url), category='success')

        except formencode.Invalid as errors:
            data = render(
                'rhodecode:templates/admin/repo_groups/repo_group_add.mako',
                self._get_template_context(c), self.request)
            html = formencode.htmlfill.render(
                data,
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8",
                force_defaults=False
            )
            return Response(html)
        except Exception:
            log.exception("Exception during creation of repository group")
            h.flash(_('Error occurred during creation of repository group %s')
                    % repo_group_name, category='error')
            raise HTTPFound(h.route_path('home'))

        PermissionModel().trigger_permission_flush()

        raise HTTPFound(
            h.route_path('repo_group_home',
                         repo_group_name=form_result['group_name_full']))
