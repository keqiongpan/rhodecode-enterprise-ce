# -*- coding: utf-8 -*-

# Copyright (C) 2011-2019 RhodeCode GmbH
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

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from rhodecode import events
from rhodecode.apps._base import BaseAppView
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (NotAnonymous, HasRepoPermissionAny)
from rhodecode.model.db import Repository
from rhodecode.model.permission import PermissionModel
from rhodecode.model.validation_schema.types import RepoNameType

log = logging.getLogger(__name__)


class RepoChecksView(BaseAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()

        return c

    @NotAnonymous()
    @view_config(
        route_name='repo_creating', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_creating.mako')
    def repo_creating(self):
        c = self.load_default_context()
        repo_name = self.request.matchdict['repo_name']
        repo_name = RepoNameType().deserialize(None, repo_name)
        db_repo = Repository.get_by_repo_name(repo_name)

        # check if maybe repo is already created
        if db_repo and db_repo.repo_state in [Repository.STATE_CREATED]:
            self.flush_permissions_on_creation(db_repo)

            # re-check permissions before redirecting to prevent resource
            # discovery by checking the 302 code
            perm_set = ['repository.read', 'repository.write', 'repository.admin']
            has_perm = HasRepoPermissionAny(*perm_set)(
                db_repo.repo_name, 'Repo Creating check')
            if not has_perm:
                raise HTTPNotFound()

            raise HTTPFound(h.route_path(
                'repo_summary', repo_name=db_repo.repo_name))

        c.task_id = self.request.GET.get('task_id')
        c.repo_name = repo_name

        return self._get_template_context(c)

    @NotAnonymous()
    @view_config(
        route_name='repo_creating_check', request_method='GET',
        renderer='json_ext')
    def repo_creating_check(self):
        _ = self.request.translate
        task_id = self.request.GET.get('task_id')
        self.load_default_context()

        repo_name = self.request.matchdict['repo_name']

        if task_id and task_id not in ['None']:
            import rhodecode
            from rhodecode.lib.celerylib.loader import celery_app, exceptions
            if rhodecode.CELERY_ENABLED:
                log.debug('celery: checking result for task:%s', task_id)
                task = celery_app.AsyncResult(task_id)
                try:
                    task.get(timeout=10)
                except exceptions.TimeoutError:
                    task = None
                if task and task.failed():
                    msg = self._log_creation_exception(task.result, repo_name)
                    h.flash(msg, category='error')
                    raise HTTPFound(h.route_path('home'), code=501)

        db_repo = Repository.get_by_repo_name(repo_name)
        if db_repo and db_repo.repo_state == Repository.STATE_CREATED:
            if db_repo.clone_uri:
                clone_uri = db_repo.clone_uri_hidden
                h.flash(_('Created repository %s from %s')
                        % (db_repo.repo_name, clone_uri), category='success')
            else:
                repo_url = h.link_to(
                    db_repo.repo_name,
                    h.route_path('repo_summary', repo_name=db_repo.repo_name))
                fork = db_repo.fork
                if fork:
                    fork_name = fork.repo_name
                    h.flash(h.literal(_('Forked repository %s as %s')
                                      % (fork_name, repo_url)), category='success')
                else:
                    h.flash(h.literal(_('Created repository %s') % repo_url),
                            category='success')
            self.flush_permissions_on_creation(db_repo)

            return {'result': True}
        return {'result': False}

    def flush_permissions_on_creation(self, db_repo):
        # repo is finished and created, we flush the permissions now
        user_group_perms = db_repo.permissions(expand_from_user_groups=True)
        affected_user_ids = [perm['user_id'] for perm in user_group_perms]
        PermissionModel().trigger_permission_flush(affected_user_ids)
