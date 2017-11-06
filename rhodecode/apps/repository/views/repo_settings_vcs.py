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
from pyramid.httpexceptions import HTTPFound, HTTPBadRequest
from pyramid.response import Response
from pyramid.renderers import render
from pyramid.view import view_config

from rhodecode.apps._base import RepoAppView
from rhodecode.lib import audit_logger
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, CSRFRequired)
from rhodecode.model.forms import RepoVcsSettingsForm
from rhodecode.model.meta import Session
from rhodecode.model.settings import VcsSettingsModel, SettingNotFound

log = logging.getLogger(__name__)


class RepoSettingsVcsView(RepoAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()

        self._register_global_c(c)
        return c

    def _vcs_form_defaults(self, repo_name):
        model = VcsSettingsModel(repo=repo_name)
        global_defaults = model.get_global_settings()

        repo_defaults = {}
        repo_defaults.update(global_defaults)
        repo_defaults.update(model.get_repo_settings())

        global_defaults = {
            '{}_inherited'.format(k): global_defaults[k]
            for k in global_defaults}

        defaults = {
            'inherit_global_settings': model.inherit_global_settings
        }
        defaults.update(global_defaults)
        defaults.update(repo_defaults)
        defaults.update({
            'new_svn_branch': '',
            'new_svn_tag': '',
        })
        return defaults

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @view_config(
        route_name='edit_repo_vcs', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def repo_vcs_settings(self):
        c = self.load_default_context()
        model = VcsSettingsModel(repo=self.db_repo_name)

        c.active = 'vcs'
        c.global_svn_branch_patterns = model.get_global_svn_branch_patterns()
        c.global_svn_tag_patterns = model.get_global_svn_tag_patterns()
        c.svn_branch_patterns = model.get_repo_svn_branch_patterns()
        c.svn_tag_patterns = model.get_repo_svn_tag_patterns()

        defaults = self._vcs_form_defaults(self.db_repo_name)
        c.inherit_global_settings = defaults['inherit_global_settings']

        data = render('rhodecode:templates/admin/repos/repo_edit.mako',
                      self._get_template_context(c), self.request)
        html = formencode.htmlfill.render(
            data,
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )
        return Response(html)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_repo_vcs_update', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def repo_settings_vcs_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'vcs'

        model = VcsSettingsModel(repo=self.db_repo_name)
        c.global_svn_branch_patterns = model.get_global_svn_branch_patterns()
        c.global_svn_tag_patterns = model.get_global_svn_tag_patterns()
        c.svn_branch_patterns = model.get_repo_svn_branch_patterns()
        c.svn_tag_patterns = model.get_repo_svn_tag_patterns()

        defaults = self._vcs_form_defaults(self.db_repo_name)
        c.inherit_global_settings = defaults['inherit_global_settings']

        application_form = RepoVcsSettingsForm(self.db_repo_name)()
        try:
            form_result = application_form.to_python(dict(self.request.POST))
        except formencode.Invalid as errors:
            h.flash(_("Some form inputs contain invalid data."),
                    category='error')

            data = render('rhodecode:templates/admin/repos/repo_edit.mako',
                          self._get_template_context(c), self.request)
            html = formencode.htmlfill.render(
                data,
                defaults=errors.value,
                errors=errors.error_dict or {},
                encoding="UTF-8",
                force_defaults=False
            )
            return Response(html)

        try:
            inherit_global_settings = form_result['inherit_global_settings']
            model.create_or_update_repo_settings(
                form_result, inherit_global_settings=inherit_global_settings)
            Session().commit()
            h.flash(_('Updated VCS settings'), category='success')
        except Exception:
            log.exception("Exception while updating settings")
            h.flash(
                _('Error occurred during updating repository VCS settings'),
                category='error')

        raise HTTPFound(
            h.route_path('edit_repo_vcs', repo_name=self.db_repo_name))

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_repo_vcs_svn_pattern_delete', request_method='POST',
        renderer='json_ext', xhr=True)
    def repo_settings_delete_svn_pattern(self):
        self.load_default_context()
        delete_pattern_id = self.request.POST.get('delete_svn_pattern')
        model = VcsSettingsModel(repo=self.db_repo_name)
        try:
            model.delete_repo_svn_pattern(delete_pattern_id)
        except SettingNotFound:
            log.exception('Failed to delete SVN pattern')
            raise HTTPBadRequest()

        Session().commit()
        return True
