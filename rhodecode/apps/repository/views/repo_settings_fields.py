# -*- coding: utf-8 -*-

# Copyright (C) 2017-2017 RhodeCode GmbH
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

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from rhodecode.apps._base import RepoAppView
from rhodecode.lib import audit_logger
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, CSRFRequired)
from rhodecode.model.db import RepositoryField
from rhodecode.model.forms import RepoFieldForm
from rhodecode.model.meta import Session
from rhodecode.model.repo import RepoModel

log = logging.getLogger(__name__)


class RepoSettingsFieldsView(RepoAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()

        self._register_global_c(c)
        return c

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @view_config(
        route_name='edit_repo_fields', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def repo_field_edit(self):
        c = self.load_default_context()

        c.active = 'fields'
        c.repo_fields = RepositoryField.query() \
            .filter(RepositoryField.repository == self.db_repo).all()

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_repo_fields_create', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def repo_field_create(self):
        _ = self.request.translate

        try:
            form_result = RepoFieldForm()().to_python(dict(self.request.POST))
            RepoModel().add_repo_field(
                self.db_repo_name,
                form_result['new_field_key'],
                field_type=form_result['new_field_type'],
                field_value=form_result['new_field_value'],
                field_label=form_result['new_field_label'],
                field_desc=form_result['new_field_desc'])

            Session().commit()
        except Exception as e:
            log.exception("Exception creating field")
            msg = _('An error occurred during creation of field')
            if isinstance(e, formencode.Invalid):
                msg += ". " + e.msg
            h.flash(msg, category='error')

        raise HTTPFound(
            h.route_path('edit_repo_fields', repo_name=self.db_repo_name))

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_repo_fields_delete', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def repo_field_delete(self):
        _ = self.request.translate
        field = RepositoryField.get_or_404(self.request.matchdict['field_id'])
        try:
            RepoModel().delete_repo_field(self.db_repo_name, field.field_key)
            Session().commit()
        except Exception:
            log.exception('Exception during removal of field')
            msg = _('An error occurred during removal of field')
            h.flash(msg, category='error')

        raise HTTPFound(
            h.route_path('edit_repo_fields', repo_name=self.db_repo_name))
