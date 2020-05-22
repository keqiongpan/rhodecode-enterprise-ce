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

import logging
import formencode
import formencode.htmlfill

from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.response import Response

from rhodecode import events
from rhodecode.apps._base import BaseAppView, DataGridAppView
from rhodecode.lib.celerylib.utils import get_task_id

from rhodecode.lib.auth import (
    LoginRequired, CSRFRequired, NotAnonymous,
    HasPermissionAny, HasRepoGroupPermissionAny)
from rhodecode.lib import helpers as h
from rhodecode.lib.utils import repo_name_slug
from rhodecode.lib.utils2 import safe_int, safe_unicode
from rhodecode.model.forms import RepoForm
from rhodecode.model.permission import PermissionModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.scm import RepoList, RepoGroupList, ScmModel
from rhodecode.model.settings import SettingsModel
from rhodecode.model.db import (
    in_filter_generator, or_, func, Session, Repository, RepoGroup, User)

log = logging.getLogger(__name__)


class AdminReposView(BaseAppView, DataGridAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()

        return c

    def _load_form_data(self, c):
        acl_groups = RepoGroupList(RepoGroup.query().all(),
                                   perm_set=['group.write', 'group.admin'])
        c.repo_groups = RepoGroup.groups_choices(groups=acl_groups)
        c.repo_groups_choices = map(lambda k: safe_unicode(k[0]), c.repo_groups)
        c.personal_repo_group = self._rhodecode_user.personal_repo_group

    @LoginRequired()
    @NotAnonymous()
    # perms check inside
    @view_config(
        route_name='repos', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repos.mako')
    def repository_list(self):
        c = self.load_default_context()
        return self._get_template_context(c)

    @LoginRequired()
    @NotAnonymous()
    # perms check inside
    @view_config(
        route_name='repos_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def repository_list_data(self):
        self.load_default_context()
        column_map = {
            'name': 'repo_name',
            'desc': 'description',
            'last_change': 'updated_on',
            'owner': 'user_username',
        }
        draw, start, limit = self._extract_chunk(self.request)
        search_q, order_by, order_dir = self._extract_ordering(
            self.request, column_map=column_map)

        _perms = ['repository.admin']
        allowed_ids = [-1] + self._rhodecode_user.repo_acl_ids_from_stack(_perms)

        repos_data_total_count = Repository.query() \
            .filter(or_(
                # generate multiple IN to fix limitation problems
                *in_filter_generator(Repository.repo_id, allowed_ids))
            ) \
            .count()

        base_q = Session.query(
            Repository.repo_id,
            Repository.repo_name,
            Repository.description,
            Repository.repo_type,
            Repository.repo_state,
            Repository.private,
            Repository.archived,
            Repository.fork,
            Repository.updated_on,
            Repository._changeset_cache,
            User,
            ) \
            .filter(or_(
                # generate multiple IN to fix limitation problems
                *in_filter_generator(Repository.repo_id, allowed_ids))
            ) \
            .join(User, User.user_id == Repository.user_id) \
            .group_by(Repository, User)

        if search_q:
            like_expression = u'%{}%'.format(safe_unicode(search_q))
            base_q = base_q.filter(or_(
                Repository.repo_name.ilike(like_expression),
            ))

        repos_data_total_filtered_count = base_q.count()

        sort_defined = False
        if order_by == 'repo_name':
            sort_col = func.lower(Repository.repo_name)
            sort_defined = True
        elif order_by == 'user_username':
            sort_col = User.username
        else:
            sort_col = getattr(Repository, order_by, None)

        if sort_defined or sort_col:
            if order_dir == 'asc':
                sort_col = sort_col.asc()
            else:
                sort_col = sort_col.desc()

        base_q = base_q.order_by(sort_col)
        base_q = base_q.offset(start).limit(limit)

        repos_list = base_q.all()

        repos_data = RepoModel().get_repos_as_dict(
            repo_list=repos_list, admin=True, super_user_actions=True)

        data = ({
            'draw': draw,
            'data': repos_data,
            'recordsTotal': repos_data_total_count,
            'recordsFiltered': repos_data_total_filtered_count,
        })
        return data

    @LoginRequired()
    @NotAnonymous()
    # perms check inside
    @view_config(
        route_name='repo_new', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_add.mako')
    def repository_new(self):
        c = self.load_default_context()

        new_repo = self.request.GET.get('repo', '')
        parent_group = safe_int(self.request.GET.get('parent_group'))
        _gr = RepoGroup.get(parent_group)

        if not HasPermissionAny('hg.admin', 'hg.create.repository')():
            # you're not super admin nor have global create permissions,
            # but maybe you have at least write permission to a parent group ?

            gr_name = _gr.group_name if _gr else None
            # create repositories with write permission on group is set to true
            create_on_write = HasPermissionAny('hg.create.write_on_repogroup.true')()
            group_admin = HasRepoGroupPermissionAny('group.admin')(group_name=gr_name)
            group_write = HasRepoGroupPermissionAny('group.write')(group_name=gr_name)
            if not (group_admin or (group_write and create_on_write)):
                raise HTTPForbidden()

        self._load_form_data(c)
        c.new_repo = repo_name_slug(new_repo)

        # apply the defaults from defaults page
        defaults = SettingsModel().get_default_repo_settings(strip_prefix=True)
        # set checkbox to autochecked
        defaults['repo_copy_permissions'] = True

        parent_group_choice = '-1'
        if not self._rhodecode_user.is_admin and self._rhodecode_user.personal_repo_group:
            parent_group_choice = self._rhodecode_user.personal_repo_group

        if parent_group and _gr:
            if parent_group in [x[0] for x in c.repo_groups]:
                parent_group_choice = safe_unicode(parent_group)

        defaults.update({'repo_group': parent_group_choice})

        data = render('rhodecode:templates/admin/repos/repo_add.mako',
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
    # perms check inside
    @view_config(
        route_name='repo_create', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repos.mako')
    def repository_create(self):
        c = self.load_default_context()

        form_result = {}
        self._load_form_data(c)

        try:
            # CanWriteToGroup validators checks permissions of this POST
            form = RepoForm(
                self.request.translate, repo_groups=c.repo_groups_choices)()
            form_result = form.to_python(dict(self.request.POST))
            copy_permissions = form_result.get('repo_copy_permissions')
            # create is done sometimes async on celery, db transaction
            # management is handled there.
            task = RepoModel().create(form_result, self._rhodecode_user.user_id)
            task_id = get_task_id(task)
        except formencode.Invalid as errors:
            data = render('rhodecode:templates/admin/repos/repo_add.mako',
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

        except Exception as e:
            msg = self._log_creation_exception(e, form_result.get('repo_name'))
            h.flash(msg, category='error')
            raise HTTPFound(h.route_path('home'))

        repo_name = form_result.get('repo_name_full')

        affected_user_ids = [self._rhodecode_user.user_id]
        if copy_permissions:
            # permission flush is done in repo creating
            pass
        PermissionModel().trigger_permission_flush(affected_user_ids)

        raise HTTPFound(
            h.route_path('repo_creating', repo_name=repo_name,
                         _query=dict(task_id=task_id)))
