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

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from rhodecode.apps._base import RepoGroupAppView
from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import (
    LoginRequired, CSRFRequired, HasRepoGroupPermissionAnyDecorator)
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


class RepoGroupSettingsView(RepoGroupAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        self._register_global_c(c)
        return c

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator('group.admin')
    @view_config(
        route_name='edit_repo_group_advanced', request_method='GET',
        renderer='rhodecode:templates/admin/repo_groups/repo_group_edit.mako')
    def edit_repo_group_advanced(self):
        c = self.load_default_context()
        c.active = 'advanced'
        c.repo_group = self.db_repo_group
        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator('group.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_repo_group_advanced_delete', request_method='POST',
        renderer='rhodecode:templates/admin/repo_groups/repo_group_edit.mako')
    def edit_repo_group_delete(self):
        _ = self.request.translate
        _ungettext = self.request.plularize
        c = self.load_default_context()
        c.repo_group = self.db_repo_group

        repos = c.repo_group.repositories.all()
        if repos:
            msg = _ungettext(
                'This repository group contains %(num)d repository and cannot be deleted',
                'This repository group contains %(num)d repositories and cannot be'
                ' deleted',
                len(repos)) % {'num': len(repos)}
            h.flash(msg, category='warning')
            raise HTTPFound(
                h.route_path('edit_repo_group_advanced',
                             repo_group_name=self.db_repo_group_name))

        children = c.repo_group.children.all()
        if children:
            msg = _ungettext(
                'This repository group contains %(num)d subgroup and cannot be deleted',
                'This repository group contains %(num)d subgroups and cannot be deleted',
                len(children)) % {'num': len(children)}
            h.flash(msg, category='warning')
            raise HTTPFound(
                h.route_path('edit_repo_group_advanced',
                             repo_group_name=self.db_repo_group_name))

        try:
            old_values = c.repo_group.get_api_data()
            RepoGroupModel().delete(self.db_repo_group_name)

            audit_logger.store_web(
                'repo_group.delete', action_data={'old_data': old_values},
                user=c.rhodecode_user)

            Session().commit()
            h.flash(_('Removed repository group `%s`') % self.db_repo_group_name,
                    category='success')
        except Exception:
            log.exception("Exception during deletion of repository group")
            h.flash(_('Error occurred during deletion of repository group %s')
                    % self.db_repo_group_name, category='error')

        raise HTTPFound(h.route_path('repo_groups'))
