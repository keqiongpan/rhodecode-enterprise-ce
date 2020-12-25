# -*- coding: utf-8 -*-

# Copyright (C) 2017-2020 RhodeCode GmbH
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

from pyramid.httpexceptions import HTTPFound, HTTPNotFound

import formencode

from rhodecode.apps._base import RepoAppView
from rhodecode.lib import audit_logger
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, CSRFRequired)
from rhodecode.model.forms import IssueTrackerPatternsForm
from rhodecode.model.meta import Session
from rhodecode.model.settings import SettingsModel

log = logging.getLogger(__name__)


class RepoSettingsIssueTrackersView(RepoAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()


        return c

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    def repo_issuetracker(self):
        c = self.load_default_context()
        c.active = 'issuetracker'
        c.data = 'data'

        c.settings_model = self.db_repo_patterns
        c.global_patterns = c.settings_model.get_global_settings()
        c.repo_patterns = c.settings_model.get_repo_settings()

        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    def repo_issuetracker_test(self):
        return h.urlify_commit_message(
            self.request.POST.get('test_text', ''),
            self.db_repo_name)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    def repo_issuetracker_delete(self):
        _ = self.request.translate
        uid = self.request.POST.get('uid')
        repo_settings = self.db_repo_patterns
        try:
            repo_settings.delete_entries(uid)
        except Exception:
            h.flash(_('Error occurred during deleting issue tracker entry'),
                    category='error')
            raise HTTPNotFound()

        SettingsModel().invalidate_settings_cache()
        h.flash(_('Removed issue tracker entry.'), category='success')

        return {'deleted': uid}

    def _update_patterns(self, form, repo_settings):
        for uid in form['delete_patterns']:
            repo_settings.delete_entries(uid)

        for pattern_data in form['patterns']:
            for setting_key, pattern, type_ in pattern_data:
                sett = repo_settings.create_or_update_setting(
                    setting_key, pattern.strip(), type_)
                Session().add(sett)

            Session().commit()

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    def repo_issuetracker_update(self):
        _ = self.request.translate
        # Save inheritance
        repo_settings = self.db_repo_patterns
        inherited = (
            self.request.POST.get('inherit_global_issuetracker') == "inherited")
        repo_settings.inherit_global_settings = inherited
        Session().commit()

        try:
            form = IssueTrackerPatternsForm(self.request.translate)().to_python(self.request.POST)
        except formencode.Invalid as errors:
            log.exception('Failed to add new pattern')
            error = errors
            h.flash(_('Invalid issue tracker pattern: {}'.format(error)),
                    category='error')
            raise HTTPFound(
                h.route_path('edit_repo_issuetracker',
                             repo_name=self.db_repo_name))

        if form:
            self._update_patterns(form, repo_settings)

        h.flash(_('Updated issue tracker entries'), category='success')
        raise HTTPFound(
            h.route_path('edit_repo_issuetracker', repo_name=self.db_repo_name))

