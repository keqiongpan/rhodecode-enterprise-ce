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

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from rhodecode import events
from rhodecode.apps._base import RepoAppView
from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, CSRFRequired)
from rhodecode.lib.utils2 import safe_int
from rhodecode.model.db import UserGroup
from rhodecode.model.forms import RepoPermsForm
from rhodecode.model.meta import Session
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
        c = self.load_default_context()
        c.active = 'permissions'
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
        h.flash(_('Repository permissions updated'), category='success')

        affected_user_ids = []
        for change in changes['added'] + changes['updated'] + changes['deleted']:
            if change['type'] == 'user':
                affected_user_ids.append(change['id'])
            if change['type'] == 'user_group':
                user_group = UserGroup.get(safe_int(change['id']))
                if user_group:
                    group_members_ids = [x.user_id for x in user_group.members]
                    affected_user_ids.extend(group_members_ids)

        events.trigger(events.UserPermissionsChange(affected_user_ids))

        raise HTTPFound(
            h.route_path('edit_repo_perms', repo_name=self.db_repo_name))
