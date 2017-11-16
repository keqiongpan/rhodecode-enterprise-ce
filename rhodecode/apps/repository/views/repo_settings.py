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

import deform
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from rhodecode.apps._base import RepoAppView
from rhodecode.forms import RcForm
from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import (
    LoginRequired, HasRepoPermissionAnyDecorator, CSRFRequired)
from rhodecode.model.db import RepositoryField, RepoGroup, Repository
from rhodecode.model.meta import Session
from rhodecode.model.repo import RepoModel
from rhodecode.model.scm import RepoGroupList, ScmModel
from rhodecode.model.validation_schema.schemas import repo_schema

log = logging.getLogger(__name__)


class RepoSettingsView(RepoAppView):

    def load_default_context(self):
        c = self._get_local_tmpl_context()

        acl_groups = RepoGroupList(
            RepoGroup.query().all(),
            perm_set=['group.write', 'group.admin'])
        c.repo_groups = RepoGroup.groups_choices(groups=acl_groups)
        c.repo_groups_choices = map(lambda k: k[0], c.repo_groups)

        # in case someone no longer have a group.write access to a repository
        # pre fill the list with this entry, we don't care if this is the same
        # but it will allow saving repo data properly.
        repo_group = self.db_repo.group
        if repo_group and repo_group.group_id not in c.repo_groups_choices:
            c.repo_groups_choices.append(repo_group.group_id)
            c.repo_groups.append(RepoGroup._generate_choice(repo_group))

        if c.repository_requirements_missing or self.rhodecode_vcs_repo is None:
            # we might be in missing requirement state, so we load things
            # without touching scm_instance()
            c.landing_revs_choices, c.landing_revs = \
                ScmModel().get_repo_landing_revs(self.request.translate)
        else:
            c.landing_revs_choices, c.landing_revs = \
                ScmModel().get_repo_landing_revs(
                    self.request.translate, self.db_repo)

        c.personal_repo_group = c.auth_user.personal_repo_group
        c.repo_fields = RepositoryField.query()\
            .filter(RepositoryField.repository == self.db_repo).all()


        return c

    def _get_schema(self, c, old_values=None):
        return repo_schema.RepoSettingsSchema().bind(
            repo_type=self.db_repo.repo_type,
            repo_type_options=[self.db_repo.repo_type],
            repo_ref_options=c.landing_revs_choices,
            repo_ref_items=c.landing_revs,
            repo_repo_group_options=c.repo_groups_choices,
            repo_repo_group_items=c.repo_groups,
            # user caller
            user=self._rhodecode_user,
            old_values=old_values
        )

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @view_config(
        route_name='edit_repo', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def edit_settings(self):
        c = self.load_default_context()
        c.active = 'settings'

        defaults = RepoModel()._get_defaults(self.db_repo_name)
        defaults['repo_owner'] = defaults['user']
        defaults['repo_landing_commit_ref'] = defaults['repo_landing_rev']

        schema = self._get_schema(c)
        c.form = RcForm(schema, appstruct=defaults)
        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_repo', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def edit_settings_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'settings'
        old_repo_name = self.db_repo_name

        old_values = self.db_repo.get_api_data()
        schema = self._get_schema(c, old_values=old_values)

        c.form = RcForm(schema)
        pstruct = self.request.POST.items()
        pstruct.append(('repo_type', self.db_repo.repo_type))
        try:
            schema_data = c.form.validate(pstruct)
        except deform.ValidationFailure as err_form:
            return self._get_template_context(c)

        # data is now VALID, proceed with updates
        # save validated data back into the updates dict
        validated_updates = dict(
            repo_name=schema_data['repo_group']['repo_name_without_group'],
            repo_group=schema_data['repo_group']['repo_group_id'],

            user=schema_data['repo_owner'],
            repo_description=schema_data['repo_description'],
            repo_private=schema_data['repo_private'],
            clone_uri=schema_data['repo_clone_uri'],
            repo_landing_rev=schema_data['repo_landing_commit_ref'],
            repo_enable_statistics=schema_data['repo_enable_statistics'],
            repo_enable_locking=schema_data['repo_enable_locking'],
            repo_enable_downloads=schema_data['repo_enable_downloads'],
        )
        # detect if CLONE URI changed, if we get OLD means we keep old values
        if schema_data['repo_clone_uri_change'] == 'OLD':
            validated_updates['clone_uri'] = self.db_repo.clone_uri

        # use the new full name for redirect
        new_repo_name = schema_data['repo_group']['repo_name_with_group']

        # save extra fields into our validated data
        for key, value in pstruct:
            if key.startswith(RepositoryField.PREFIX):
                validated_updates[key] = value

        try:
            RepoModel().update(self.db_repo, **validated_updates)
            ScmModel().mark_for_invalidation(new_repo_name)

            audit_logger.store_web(
                'repo.edit', action_data={'old_data': old_values},
                user=self._rhodecode_user, repo=self.db_repo)

            Session().commit()

            h.flash(_('Repository `{}` updated successfully').format(
                old_repo_name), category='success')
        except Exception:
            log.exception("Exception during update of repository")
            h.flash(_('Error occurred during update of repository {}').format(
                old_repo_name), category='error')

        raise HTTPFound(
            h.route_path('edit_repo', repo_name=new_repo_name))

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.write', 'repository.admin')
    @view_config(
        route_name='repo_edit_toggle_locking', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def toggle_locking(self):
        """
        Toggle locking of repository by simple GET call to url
        """
        _ = self.request.translate
        repo = self.db_repo

        try:
            if repo.enable_locking:
                if repo.locked[0]:
                    Repository.unlock(repo)
                    action = _('Unlocked')
                else:
                    Repository.lock(
                        repo, self._rhodecode_user.user_id,
                        lock_reason=Repository.LOCK_WEB)
                    action = _('Locked')

                h.flash(_('Repository has been %s') % action,
                        category='success')
        except Exception:
            log.exception("Exception during unlocking")
            h.flash(_('An error occurred during unlocking'),
                    category='error')
        raise HTTPFound(
            h.route_path('repo_summary', repo_name=self.db_repo_name))

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @view_config(
        route_name='edit_repo_statistics', request_method='GET',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def edit_statistics_form(self):
        c = self.load_default_context()

        if self.db_repo.stats:
            # this is on what revision we ended up so we add +1 for count
            last_rev = self.db_repo.stats.stat_on_revision + 1
        else:
            last_rev = 0

        c.active = 'statistics'
        c.stats_revision = last_rev
        c.repo_last_rev = self.rhodecode_vcs_repo.count()

        if last_rev == 0 or c.repo_last_rev == 0:
            c.stats_percentage = 0
        else:
            c.stats_percentage = '%.2f' % (
            (float((last_rev)) / c.repo_last_rev) * 100)
        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_repo_statistics_reset', request_method='POST',
        renderer='rhodecode:templates/admin/repos/repo_edit.mako')
    def repo_statistics_reset(self):
        _ = self.request.translate

        try:
            RepoModel().delete_stats(self.db_repo_name)
            Session().commit()
        except Exception:
            log.exception('Edit statistics failure')
            h.flash(_('An error occurred during deletion of repository stats'),
                    category='error')
        raise HTTPFound(
            h.route_path('edit_repo_statistics', repo_name=self.db_repo_name))
