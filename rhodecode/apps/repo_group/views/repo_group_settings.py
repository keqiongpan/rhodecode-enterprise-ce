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

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from rhodecode.apps._base import RepoGroupAppView
from rhodecode.forms import RcForm
from rhodecode.lib import helpers as h
from rhodecode.lib import audit_logger
from rhodecode.lib.auth import (
    LoginRequired, HasPermissionAll,
    HasRepoGroupPermissionAny, HasRepoGroupPermissionAnyDecorator, CSRFRequired)
from rhodecode.model.db import Session, RepoGroup
from rhodecode.model.scm import RepoGroupList
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.validation_schema.schemas import repo_group_schema

log = logging.getLogger(__name__)


class RepoGroupSettingsView(RepoGroupAppView):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.repo_group = self.db_repo_group
        no_parrent = not c.repo_group.parent_group
        can_create_in_root = self._can_create_repo_group()

        show_root_location = False
        if no_parrent or can_create_in_root:
            # we're global admin, we're ok and we can create TOP level groups
            # or in case this group is already at top-level we also allow
            # creation in root
            show_root_location = True

        acl_groups = RepoGroupList(
            RepoGroup.query().all(),
            perm_set=['group.admin'])
        c.repo_groups = RepoGroup.groups_choices(
            groups=acl_groups,
            show_empty_group=show_root_location)
        # filter out current repo group
        exclude_group_ids = [c.repo_group.group_id]
        c.repo_groups = filter(lambda x: x[0] not in exclude_group_ids,
                               c.repo_groups)
        c.repo_groups_choices = map(lambda k: k[0], c.repo_groups)

        parent_group = c.repo_group.parent_group

        add_parent_group = (parent_group and (
            parent_group.group_id not in c.repo_groups_choices))
        if add_parent_group:
            c.repo_groups_choices.append(parent_group.group_id)
            c.repo_groups.append(RepoGroup._generate_choice(parent_group))


        return c

    def _can_create_repo_group(self, parent_group_id=None):
        is_admin = HasPermissionAll('hg.admin')('group create controller')
        create_repo_group = HasPermissionAll(
            'hg.repogroup.create.true')('group create controller')
        if is_admin or (create_repo_group and not parent_group_id):
            # we're global admin, or we have global repo group create
            # permission
            # we're ok and we can create TOP level groups
            return True
        elif parent_group_id:
            # we check the permission if we can write to parent group
            group = RepoGroup.get(parent_group_id)
            group_name = group.group_name if group else None
            if HasRepoGroupPermissionAny('group.admin')(
                    group_name, 'check if user is an admin of group'):
                # we're an admin of passed in group, we're ok.
                return True
            else:
                return False
        return False

    def _get_schema(self, c, old_values=None):
        return repo_group_schema.RepoGroupSettingsSchema().bind(
            repo_group_repo_group_options=c.repo_groups_choices,
            repo_group_repo_group_items=c.repo_groups,

            # user caller
            user=self._rhodecode_user,
            old_values=old_values
        )

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator('group.admin')
    @view_config(
        route_name='edit_repo_group', request_method='GET',
        renderer='rhodecode:templates/admin/repo_groups/repo_group_edit.mako')
    def edit_settings(self):
        c = self.load_default_context()
        c.active = 'settings'

        defaults = RepoGroupModel()._get_defaults(self.db_repo_group_name)
        defaults['repo_group_owner'] = defaults['user']

        schema = self._get_schema(c)
        c.form = RcForm(schema, appstruct=defaults)
        return self._get_template_context(c)

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator('group.admin')
    @CSRFRequired()
    @view_config(
        route_name='edit_repo_group', request_method='POST',
        renderer='rhodecode:templates/admin/repo_groups/repo_group_edit.mako')
    def edit_settings_update(self):
        _ = self.request.translate
        c = self.load_default_context()
        c.active = 'settings'

        old_repo_group_name = self.db_repo_group_name
        new_repo_group_name = old_repo_group_name

        old_values = RepoGroupModel()._get_defaults(self.db_repo_group_name)
        schema = self._get_schema(c, old_values=old_values)

        c.form = RcForm(schema)
        pstruct = self.request.POST.items()

        try:
            schema_data = c.form.validate(pstruct)
        except deform.ValidationFailure as err_form:
            return self._get_template_context(c)

        # data is now VALID, proceed with updates
        # save validated data back into the updates dict
        validated_updates = dict(
            group_name=schema_data['repo_group']['repo_group_name_without_group'],
            group_parent_id=schema_data['repo_group']['repo_group_id'],
            user=schema_data['repo_group_owner'],
            group_description=schema_data['repo_group_description'],
            enable_locking=schema_data['repo_group_enable_locking'],
        )

        try:
            RepoGroupModel().update(self.db_repo_group, validated_updates)

            audit_logger.store_web(
                'repo_group.edit', action_data={'old_data': old_values},
                user=c.rhodecode_user)

            Session().commit()

            # use the new full name for redirect once we know we updated
            # the name on filesystem and in DB
            new_repo_group_name = schema_data['repo_group']['repo_group_name_with_group']

            h.flash(_('Repository Group `{}` updated successfully').format(
                old_repo_group_name), category='success')

        except Exception:
            log.exception("Exception during update or repository group")
            h.flash(_('Error occurred during update of repository group %s')
                    % old_repo_group_name, category='error')

        raise HTTPFound(
            h.route_path('edit_repo_group', repo_group_name=new_repo_group_name))
