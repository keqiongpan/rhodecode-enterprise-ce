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

from rhodecode.apps._base import RepoGroupAppView
from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import (
    LoginRequired, HasRepoGroupPermissionAnyDecorator, CSRFRequired)
from rhodecode.model.db import User
from rhodecode.model.permission import PermissionModel
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.forms import RepoGroupPermsForm
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


class RepoGroupPermissionsView(RepoGroupAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()

        return c

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator('group.admin')
    def edit_repo_group_permissions(self):
        c = self.load_default_context()
        c.active = 'permissions'
        c.repo_group = self.db_repo_group
        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator('group.admin')
    @CSRFRequired()
    def edit_repo_groups_permissions_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'perms'
        c.repo_group = self.db_repo_group

        valid_recursive_choices = ['none', 'repos', 'groups', 'all']
        form = RepoGroupPermsForm(self.request.translate, valid_recursive_choices)()\
            .to_python(self.request.POST)

        if not c.rhodecode_user.is_admin:
            if self._revoke_perms_on_yourself(form):
                msg = _('Cannot change permission for yourself as admin')
                h.flash(msg, category='warning')
                raise HTTPFound(
                    h.route_path('edit_repo_group_perms',
                                 repo_group_name=self.db_repo_group_name))

        # iterate over all members(if in recursive mode) of this groups and
        # set the permissions !
        # this can be potentially heavy operation
        changes = RepoGroupModel().update_permissions(
            c.repo_group,
            form['perm_additions'], form['perm_updates'], form['perm_deletions'],
            form['recursive'])

        action_data = {
            'added': changes['added'],
            'updated': changes['updated'],
            'deleted': changes['deleted'],
        }
        audit_logger.store_web(
            'repo_group.edit.permissions', action_data=action_data,
            user=c.rhodecode_user)

        Session().commit()
        h.flash(_('Repository Group permissions updated'), category='success')

        affected_user_ids = None
        if changes.get('default_user_changed', False):
            # if we change the default user, we need to flush everyone permissions
            affected_user_ids = User.get_all_user_ids()
        PermissionModel().flush_user_permission_caches(
            changes, affected_user_ids=affected_user_ids)

        raise HTTPFound(
            h.route_path('edit_repo_group_perms',
                         repo_group_name=self.db_repo_group_name))
