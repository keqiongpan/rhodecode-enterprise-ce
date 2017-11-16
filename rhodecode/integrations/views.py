# -*- coding: utf-8 -*-

# Copyright (C) 2012-2017 RhodeCode GmbH
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

import deform
import logging
import peppercorn
import webhelpers.paginate

from pyramid.httpexceptions import HTTPFound, HTTPForbidden, HTTPNotFound

from rhodecode.apps._base import BaseAppView
from rhodecode.integrations import integration_type_registry
from rhodecode.apps.admin.navigation import navigation_list
from rhodecode.lib.auth import (
    LoginRequired, CSRFRequired, HasPermissionAnyDecorator,
    HasRepoPermissionAnyDecorator, HasRepoGroupPermissionAnyDecorator)
from rhodecode.lib.utils2 import safe_int
from rhodecode.lib import helpers as h
from rhodecode.model.db import Repository, RepoGroup, Session, Integration
from rhodecode.model.scm import ScmModel
from rhodecode.model.integration import IntegrationModel
from rhodecode.model.validation_schema.schemas.integration_schema import (
    make_integration_schema, IntegrationScopeType)

log = logging.getLogger(__name__)


class IntegrationSettingsViewBase(BaseAppView):
    """
    Base Integration settings view used by both repo / global settings
    """

    def __init__(self, context, request):
        super(IntegrationSettingsViewBase, self).__init__(context, request)
        self._load_view_context()

    def _load_view_context(self):
        """
        This avoids boilerplate for repo/global+list/edit+views/templates
        by doing all possible contexts at the same time however it should
        be split up into separate functions once more "contexts" exist
        """

        self.IntegrationType = None
        self.repo = None
        self.repo_group = None
        self.integration = None
        self.integrations = {}

        request = self.request

        if 'repo_name' in request.matchdict:  # in repo settings context
            repo_name = request.matchdict['repo_name']
            self.repo = Repository.get_by_repo_name(repo_name)

        if 'repo_group_name' in request.matchdict:  # in group settings context
            repo_group_name = request.matchdict['repo_group_name']
            self.repo_group = RepoGroup.get_by_group_name(repo_group_name)

        if 'integration' in request.matchdict:  # integration type context
            integration_type = request.matchdict['integration']
            if integration_type not in integration_type_registry:
                raise HTTPNotFound()

            self.IntegrationType = integration_type_registry[integration_type]
            if self.IntegrationType.is_dummy:
                raise HTTPNotFound()

        if 'integration_id' in request.matchdict:  # single integration context
            integration_id = request.matchdict['integration_id']
            self.integration = Integration.get(integration_id)

            # extra perms check just in case
            if not self._has_perms_for_integration(self.integration):
                raise HTTPForbidden()

        self.settings = self.integration and self.integration.settings or {}
        self.admin_view = not (self.repo or self.repo_group)

    def _has_perms_for_integration(self, integration):
        perms = self.request.user.permissions

        if 'hg.admin' in perms['global']:
            return True

        if integration.repo:
            return perms['repositories'].get(
                integration.repo.repo_name) == 'repository.admin'

        if integration.repo_group:
            return perms['repositories_groups'].get(
                integration.repo_group.group_name) == 'group.admin'

        return False

    def _get_local_tmpl_context(self, include_app_defaults=True):
        _ = self.request.translate
        c = super(IntegrationSettingsViewBase, self)._get_local_tmpl_context(
            include_app_defaults=include_app_defaults)

        c.active = 'integrations'

        return c

    def _form_schema(self):
        schema = make_integration_schema(IntegrationType=self.IntegrationType,
                                         settings=self.settings)

        # returns a clone, important if mutating the schema later
        return schema.bind(
            permissions=self.request.user.permissions,
            no_scope=not self.admin_view)

    def _form_defaults(self):
        _ = self.request.translate
        defaults = {}

        if self.integration:
            defaults['settings'] = self.integration.settings or {}
            defaults['options'] = {
                'name': self.integration.name,
                'enabled': self.integration.enabled,
                'scope': {
                    'repo': self.integration.repo,
                    'repo_group': self.integration.repo_group,
                    'child_repos_only': self.integration.child_repos_only,
                },
            }
        else:
            if self.repo:
                scope = _('{repo_name} repository').format(
                    repo_name=self.repo.repo_name)
            elif self.repo_group:
                scope = _('{repo_group_name} repo group').format(
                    repo_group_name=self.repo_group.group_name)
            else:
                scope = _('Global')

            defaults['options'] = {
                'enabled': True,
                'name': _('{name} integration').format(
                    name=self.IntegrationType.display_name),
            }
            defaults['options']['scope'] = {
                'repo': self.repo,
                'repo_group': self.repo_group,
            }

        return defaults

    def _delete_integration(self, integration):
        _ = self.request.translate
        Session().delete(integration)
        Session().commit()
        h.flash(
            _('Integration {integration_name} deleted successfully.').format(
                integration_name=integration.name),
            category='success')

        if self.repo:
            redirect_to = self.request.route_path(
                'repo_integrations_home', repo_name=self.repo.repo_name)
        elif self.repo_group:
            redirect_to = self.request.route_path(
                'repo_group_integrations_home',
                repo_group_name=self.repo_group.group_name)
        else:
            redirect_to = self.request.route_path('global_integrations_home')
        raise HTTPFound(redirect_to)

    def _integration_list(self):
        """ List integrations """

        c = self.load_default_context()
        if self.repo:
            scope = self.repo
        elif self.repo_group:
            scope = self.repo_group
        else:
            scope = 'all'

        integrations = []

        for IntType, integration in IntegrationModel().get_integrations(
                        scope=scope, IntegrationType=self.IntegrationType):

            # extra permissions check *just in case*
            if not self._has_perms_for_integration(integration):
                continue

            integrations.append((IntType, integration))

        sort_arg = self.request.GET.get('sort', 'name:asc')
        sort_dir = 'asc'
        if ':' in sort_arg:
            sort_field, sort_dir = sort_arg.split(':')
        else:
            sort_field = sort_arg, 'asc'

        assert sort_field in ('name', 'integration_type', 'enabled', 'scope')

        integrations.sort(
            key=lambda x: getattr(x[1], sort_field),
            reverse=(sort_dir == 'desc'))

        page_url = webhelpers.paginate.PageURL(
            self.request.path, self.request.GET)
        page = safe_int(self.request.GET.get('page', 1), 1)

        integrations = h.Page(
            integrations, page=page, items_per_page=10, url=page_url)

        c.rev_sort_dir = sort_dir != 'desc' and 'desc' or 'asc'

        c.current_IntegrationType = self.IntegrationType
        c.integrations_list = integrations
        c.available_integrations = integration_type_registry

        return self._get_template_context(c)

    def _settings_get(self, defaults=None, form=None):
        """
        View that displays the integration settings as a form.
        """
        c = self.load_default_context()

        defaults = defaults or self._form_defaults()
        schema = self._form_schema()

        if self.integration:
            buttons = ('submit', 'delete')
        else:
            buttons = ('submit',)

        form = form or deform.Form(schema, appstruct=defaults, buttons=buttons)

        c.form = form
        c.current_IntegrationType = self.IntegrationType
        c.integration = self.integration

        return self._get_template_context(c)

    def _settings_post(self):
        """
        View that validates and stores the integration settings.
        """
        _ = self.request.translate

        controls = self.request.POST.items()
        pstruct = peppercorn.parse(controls)

        if self.integration and pstruct.get('delete'):
            return self._delete_integration(self.integration)

        schema = self._form_schema()

        skip_settings_validation = False
        if self.integration and 'enabled' not in pstruct.get('options', {}):
            skip_settings_validation = True
            schema['settings'].validator = None
            for field in schema['settings'].children:
                field.validator = None
                field.missing = ''

        if self.integration:
            buttons = ('submit', 'delete')
        else:
            buttons = ('submit',)

        form = deform.Form(schema, buttons=buttons)

        if not self.admin_view:
            # scope is read only field in these cases, and has to be added
            options = pstruct.setdefault('options', {})
            if 'scope' not in options:
                options['scope'] = IntegrationScopeType().serialize(None, {
                    'repo': self.repo,
                    'repo_group': self.repo_group,
                })

        try:
            valid_data = form.validate_pstruct(pstruct)
        except deform.ValidationFailure as e:
            h.flash(
                _('Errors exist when saving integration settings. '
                  'Please check the form inputs.'),
                category='error')
            return self._settings_get(form=e)

        if not self.integration:
            self.integration = Integration()
            self.integration.integration_type = self.IntegrationType.key
            Session().add(self.integration)

        scope = valid_data['options']['scope']

        IntegrationModel().update_integration(self.integration,
            name=valid_data['options']['name'],
            enabled=valid_data['options']['enabled'],
            settings=valid_data['settings'],
            repo=scope['repo'],
            repo_group=scope['repo_group'],
            child_repos_only=scope['child_repos_only'],
        )

        self.integration.settings = valid_data['settings']
        Session().commit()
        # Display success message and redirect.
        h.flash(
            _('Integration {integration_name} updated successfully.').format(
                integration_name=self.IntegrationType.display_name),
            category='success')

        # if integration scope changes, we must redirect to the right place
        # keeping in mind if the original view was for /repo/ or /_admin/
        admin_view = not (self.repo or self.repo_group)

        if self.integration.repo and not admin_view:
            redirect_to = self.request.route_path(
                'repo_integrations_edit',
                repo_name=self.integration.repo.repo_name,
                integration=self.integration.integration_type,
                integration_id=self.integration.integration_id)
        elif self.integration.repo_group and not admin_view:
            redirect_to = self.request.route_path(
                'repo_group_integrations_edit',
                repo_group_name=self.integration.repo_group.group_name,
                integration=self.integration.integration_type,
                integration_id=self.integration.integration_id)
        else:
            redirect_to = self.request.route_path(
                'global_integrations_edit',
                integration=self.integration.integration_type,
                integration_id=self.integration.integration_id)

        return HTTPFound(redirect_to)

    def _new_integration(self):
        c = self.load_default_context()
        c.available_integrations = integration_type_registry
        return self._get_template_context(c)

    def load_default_context(self):
        raise NotImplementedError()


class GlobalIntegrationsView(IntegrationSettingsViewBase):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.repo = self.repo
        c.repo_group = self.repo_group
        c.navlist = navigation_list(self.request)

        return c

    @LoginRequired()
    @HasPermissionAnyDecorator('hg.admin')
    def integration_list(self):
        return self._integration_list()

    @LoginRequired()
    @HasPermissionAnyDecorator('hg.admin')
    def settings_get(self):
        return self._settings_get()

    @LoginRequired()
    @HasPermissionAnyDecorator('hg.admin')
    @CSRFRequired()
    def settings_post(self):
        return self._settings_post()

    @LoginRequired()
    @HasPermissionAnyDecorator('hg.admin')
    def new_integration(self):
        return self._new_integration()


class RepoIntegrationsView(IntegrationSettingsViewBase):
    def load_default_context(self):
        c = self._get_local_tmpl_context()

        c.repo = self.repo
        c.repo_group = self.repo_group

        self.db_repo = self.repo
        c.rhodecode_db_repo = self.repo
        c.repo_name = self.db_repo.repo_name
        c.repository_pull_requests = ScmModel().get_pull_requests(self.repo)


        return c

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    def integration_list(self):
        return self._integration_list()

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    def settings_get(self):
        return self._settings_get()

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    @CSRFRequired()
    def settings_post(self):
        return self._settings_post()

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.admin')
    def new_integration(self):
        return self._new_integration()


class RepoGroupIntegrationsView(IntegrationSettingsViewBase):
    def load_default_context(self):
        c = self._get_local_tmpl_context()
        c.repo = self.repo
        c.repo_group = self.repo_group
        c.navlist = navigation_list(self.request)

        return c

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator('group.admin')
    def integration_list(self):
        return self._integration_list()

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator('group.admin')
    def settings_get(self):
        return self._settings_get()

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator('group.admin')
    @CSRFRequired()
    def settings_post(self):
        return self._settings_post()

    @LoginRequired()
    @HasRepoGroupPermissionAnyDecorator('group.admin')
    def new_integration(self):
        return self._new_integration()
