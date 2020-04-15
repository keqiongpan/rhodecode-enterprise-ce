# -*- coding: utf-8 -*-

# Copyright (C) 2011-2020 RhodeCode GmbH
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

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from rhodecode.apps._base import RepoAppView
from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, CSRFRequired)
from rhodecode.lib.utils2 import str2bool
from rhodecode.model.db import User
from rhodecode.model.forms import RepoPermsForm
from rhodecode.model.meta import Session
from rhodecode.model.permission import PermissionModel
from rhodecode.model.repo import RepoModel

log = logging.getLogger(__name__)


class RepoSettingsPermissionsView(RepoAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()
        return c

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @view_config(
        route_name='edit_repo_perms', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def edit_permissions(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'permissions'
        if self.request.GET.get('branch_permissions'):
            h.flash(_('Explicitly add user or user group with write+ '
                      'permission to modify their branch permissions.'),
                    category='notice')
        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_repo_perms', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def edit_permissions_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'permissions'
        data = self.request.POST
        # store private flag outside of HTML to verify if we can modify
        # default user permissions, prevents submission of FAKE post data
        # into the form for private repos
        data['repo_private'] = self.db_repo.private
        form = RepoPermsForm(self.request.translate)().to_python(data)
        changes = RepoModel().update_permissions(
            self.db_repo_name, form['perm_additions'], form['perm_updates'],
            form['perm_deletions'])

        action_data = {
            'added': changes['added'],
            'updated': changes['updated'],
            'deleted': changes['deleted'],
        }
        audit_logger.store_web(
            'repo.edit.permissions', action_data=action_data,
            user=self._rhodecode_user, repo=self.db_repo)

        Session().commit()
        h.flash(_('Repository access permissions updated'), category='success')

        affected_user_ids = None
        if changes.get('default_user_changed', False):
            # if we change the default user, we need to flush everyone permissions
            affected_user_ids = User.get_all_user_ids()
        PermissionModel().flush_user_permission_caches(
            changes, affected_user_ids=affected_user_ids)

        raise HTTPFound(
            h.route_path('edit_repo_perms', repo_name=self.db_repo_name))

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_repo_perms_set_private', request_method='POST',
        renderer='json_ext')
    def edit_permissions_set_private_repo(self):
        _ = self.request.translate
        self.load_default_context()

        private_flag = str2bool(self.request.POST.get('private'))

        try:
            RepoModel().update(
                self.db_repo, **{'repo_private': private_flag, 'repo_name': self.db_repo_name})
            Session().commit()

            h.flash(_('Repository `{}` private mode set successfully').format(self.db_repo_name),
                    category='success')
        except Exception:
            log.exception("Exception during update of repository")
            h.flash(_('Error occurred during update of repository {}').format(
                self.db_repo_name), category='error')

        # NOTE(dan): we change repo private mode we need to notify all USERS
        affected_user_ids = User.get_all_user_ids()
        PermissionModel().trigger_permission_flush(affected_user_ids)

        return {
            'redirect_url': h.route_path('edit_repo_perms', repo_name=self.db_repo_name),
            'private': private_flag
        }
