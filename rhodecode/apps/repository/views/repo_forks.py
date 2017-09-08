# -*- coding: utf-8 -*-

# Copyright (C) 2011-2017 RhodeCode GmbH
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
import datetime
import formencode
import formencode.htmlfill

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.renderers import render
from pyramid.response import Response

from rhodecode.apps._base import RepoAppView, DataGridAppView
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, NotAnonymous,
    HasRepoPermissionAny, HasPermissionAnyDecorator, CSRFRequired)
import rhodecode.lib.helpers as h
from rhodecode.model.db import coalesce, or_, Repository, RepoGroup
from rhodecode.model.repo import RepoModel
from rhodecode.model.forms import RepoForkForm
from rhodecode.model.scm import ScmModel, RepoGroupList
from rhodecode.lib.utils2 import safe_int, safe_unicode

log = logging.getLogger(__name__)


class RepoForksView(RepoAppView, DataGridAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context(include_app_defaults=True)
        c.rhodecode_repo = self.rhodecode_vcs_repo

        acl_groups = RepoGroupList(
            RepoGroup.query().all(),
            perm_set=['group.write', 'group.admin'])
        c.repo_groups = RepoGroup.groups_choices(groups=acl_groups)
        c.repo_groups_choices = map(lambda k: safe_unicode(k[0]), c.repo_groups)
        choices, c.landing_revs = ScmModel().get_repo_landing_revs()
        c.landing_revs_choices = choices
        c.personal_repo_group = c.rhodecode_user.personal_repo_group

        self._register_global_c(c)
        return c

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_forks_show_all', request_method='GET',
        renderer='rhodecode:templates/forks/forks.mako')
    def repo_forks_show_all(self):
        c = self.load_default_context()
        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_forks_data', request_method='GET',
        renderer='json_ext', xhr=True)
    def repo_forks_data(self):
        _ = self.request.translate
        column_map = {
            'fork_name': 'repo_name',
            'fork_date': 'created_on',
            'last_activity': 'updated_on'
        }
        draw, start, limit = self._extract_chunk(self.request)
        search_q, order_by, order_dir = self._extract_ordering(
            self.request, column_map=column_map)

        acl_check = HasRepoPermissionAny(
            'repository.read', 'repository.write', 'repository.admin')
        repo_id = self.db_repo.repo_id
        allowed_ids = []
        for f in Repository.query().filter(Repository.fork_id == repo_id):
            if acl_check(f.repo_name, 'get forks check'):
                allowed_ids.append(f.repo_id)

        forks_data_total_count = Repository.query()\
            .filter(Repository.fork_id == repo_id)\
            .filter(Repository.repo_id.in_(allowed_ids))\
            .count()

        # json generate
        base_q = Repository.query()\
            .filter(Repository.fork_id == repo_id)\
            .filter(Repository.repo_id.in_(allowed_ids))\

        if search_q:
            like_expression = u'%{}%'.format(safe_unicode(search_q))
            base_q = base_q.filter(or_(
                Repository.repo_name.ilike(like_expression),
                Repository.description.ilike(like_expression),
            ))

        forks_data_total_filtered_count = base_q.count()

        sort_col = getattr(Repository, order_by, None)
        if sort_col:
            if order_dir == 'asc':
                # handle null values properly to order by NULL last
                if order_by in ['last_activity']:
                    sort_col = coalesce(sort_col, datetime.date.max)
                sort_col = sort_col.asc()
            else:
                # handle null values properly to order by NULL last
                if order_by in ['last_activity']:
                    sort_col = coalesce(sort_col, datetime.date.min)
                sort_col = sort_col.desc()

        base_q = base_q.order_by(sort_col)
        base_q = base_q.offset(start).limit(limit)

        fork_list = base_q.all()

        def fork_actions(fork):
            url_link = h.route_path(
                'repo_compare',
                repo_name=fork.repo_name,
                source_ref_type=self.db_repo.landing_rev[0],
                source_ref=self.db_repo.landing_rev[1],
                target_ref_type=self.db_repo.landing_rev[0],
                target_ref=self.db_repo.landing_rev[1],
                _query=dict(merge=1, target_repo=f.repo_name))
            return h.link_to(_('Compare fork'), url_link, class_='btn-link')

        def fork_name(fork):
            return h.link_to(fork.repo_name,
                      h.route_path('repo_summary', repo_name=fork.repo_name))

        forks_data = []
        for fork in fork_list:
            forks_data.append({
                "username": h.gravatar_with_user(self.request, fork.user.username),
                "fork_name": fork_name(fork),
                "description": fork.description,
                "fork_date": h.age_component(fork.created_on, time_is_local=True),
                "last_activity": h.format_date(fork.updated_on),
                "action": fork_actions(fork),
            })

        data = ({
            'draw': draw,
            'data': forks_data,
            'recordsTotal': forks_data_total_count,
            'recordsFiltered': forks_data_total_filtered_count,
        })

        return data

    @LoginRequired()
    @NotAnonymous()
    @HasPermissionAnyDecorator('hg.admin', 'hg.fork.repository')
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @view_config(
        route_name='repo_fork_new', request_method='GET',
        renderer='rhodecode:templates/forks/forks.mako')
    def repo_fork_new(self):
        c = self.load_default_context()

        defaults = RepoModel()._get_defaults(self.db_repo_name)
        # alter the description to indicate a fork
        defaults['description'] = (
            'fork of repository: %s \n%s' % (
                defaults['repo_name'], defaults['description']))
        # add suffix to fork
        defaults['repo_name'] = '%s-fork' % defaults['repo_name']

        data = render('rhodecode:templates/forks/fork.mako',
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
    @HasPermissionAnyDecorator('hg.admin', 'hg.fork.repository')
    @HasRepoPermissionAnyDecorator(
        'repository.read', 'repository.write', 'repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='repo_fork_create', request_method='POST',
        renderer='rhodecode:templates/forks/fork.mako')
    def repo_fork_create(self):
        _ = self.request.translate
        c = self.load_default_context()

        _form = RepoForkForm(old_data={'repo_type': self.db_repo.repo_type},
                             repo_groups=c.repo_groups_choices,
                             landing_revs=c.landing_revs_choices)()
        form_result = {}
        task_id = None
        try:
            form_result = _form.to_python(dict(self.request.POST))
            # create fork is done sometimes async on celery, db transaction
            # management is handled there.
            task = RepoModel().create_fork(
                form_result, c.rhodecode_user.user_id)
            from celery.result import BaseAsyncResult
            if isinstance(task, BaseAsyncResult):
                task_id = task.task_id
        except formencode.Invalid as errors:
            c.rhodecode_db_repo = self.db_repo

            data = render('rhodecode:templates/forks/fork.mako',
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
            log.exception(
                u'Exception while trying to fork the repository %s',
                self.db_repo_name)
            msg = (
                _('An error occurred during repository forking %s') % (
                    self.db_repo_name, ))
            h.flash(msg, category='error')

        repo_name = form_result.get('repo_name_full', self.db_repo_name)
        raise HTTPFound(
            h.route_path('repo_creating',
                         repo_name=repo_name,
                         _query=dict(task_id=task_id)))
