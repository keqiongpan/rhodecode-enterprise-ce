# -*- coding: utf-8 -*-

# Copyright (C) 2012-2016  RhodeCode GmbH
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

from rhodecode.model.db import Repository, Integration, RepoGroup
from rhodecode.config.routing import (
    ADMIN_PREFIX, add_route_requirements, URL_NAME_REQUIREMENTS)
from rhodecode.integrations import integration_type_registry

log = logging.getLogger(__name__)


def includeme(config):

    # global integrations

    config.add_route('global_integrations_new',
                     ADMIN_PREFIX + '/integrations/new')
    config.add_view('rhodecode.integrations.views.GlobalIntegrationsView',
                    attr='new_integration',
                    renderer='rhodecode:templates/admin/integrations/new.html',
                    request_method='GET',
                    route_name='global_integrations_new')

    config.add_route('global_integrations_home',
                     ADMIN_PREFIX + '/integrations')
    config.add_route('global_integrations_list',
                     ADMIN_PREFIX + '/integrations/{integration}')
    for route_name in ['global_integrations_home', 'global_integrations_list']:
        config.add_view('rhodecode.integrations.views.GlobalIntegrationsView',
                        attr='index',
                        renderer='rhodecode:templates/admin/integrations/list.html',
                        request_method='GET',
                        route_name=route_name)

    config.add_route('global_integrations_create',
                     ADMIN_PREFIX + '/integrations/{integration}/new',
                     custom_predicates=(valid_integration,))
    config.add_route('global_integrations_edit',
                     ADMIN_PREFIX + '/integrations/{integration}/{integration_id}',
                     custom_predicates=(valid_integration,))


    for route_name in ['global_integrations_create', 'global_integrations_edit']:
        config.add_view('rhodecode.integrations.views.GlobalIntegrationsView',
                        attr='settings_get',
                        renderer='rhodecode:templates/admin/integrations/form.html',
                        request_method='GET',
                        route_name=route_name)
        config.add_view('rhodecode.integrations.views.GlobalIntegrationsView',
                        attr='settings_post',
                        renderer='rhodecode:templates/admin/integrations/form.html',
                        request_method='POST',
                        route_name=route_name)


    # repo group integrations
    config.add_route('repo_group_integrations_home',
                     add_route_requirements(
                        '{repo_group_name}/settings/integrations',
                        URL_NAME_REQUIREMENTS
                     ),
                     custom_predicates=(valid_repo_group,)
                     )
    config.add_route('repo_group_integrations_list',
                     add_route_requirements(
                        '{repo_group_name}/settings/integrations/{integration}',
                        URL_NAME_REQUIREMENTS
                     ),
                     custom_predicates=(valid_repo_group, valid_integration))
    for route_name in ['repo_group_integrations_home', 'repo_group_integrations_list']:
        config.add_view('rhodecode.integrations.views.RepoGroupIntegrationsView',
                        attr='index',
                        renderer='rhodecode:templates/admin/integrations/list.html',
                        request_method='GET',
                        route_name=route_name)

    config.add_route('repo_group_integrations_new',
                     add_route_requirements(
                        '{repo_group_name}/settings/integrations/new',
                        URL_NAME_REQUIREMENTS
                     ),
                     custom_predicates=(valid_repo_group,))
    config.add_view('rhodecode.integrations.views.RepoGroupIntegrationsView',
                    attr='new_integration',
                    renderer='rhodecode:templates/admin/integrations/new.html',
                    request_method='GET',
                    route_name='repo_group_integrations_new')

    config.add_route('repo_group_integrations_create',
                     add_route_requirements(
                        '{repo_group_name}/settings/integrations/{integration}/new',
                        URL_NAME_REQUIREMENTS
                     ),
                     custom_predicates=(valid_repo_group, valid_integration))
    config.add_route('repo_group_integrations_edit',
                     add_route_requirements(
                        '{repo_group_name}/settings/integrations/{integration}/{integration_id}',
                        URL_NAME_REQUIREMENTS
                     ),
                     custom_predicates=(valid_repo_group, valid_integration))
    for route_name in ['repo_group_integrations_edit', 'repo_group_integrations_create']:
        config.add_view('rhodecode.integrations.views.RepoGroupIntegrationsView',
                        attr='settings_get',
                        renderer='rhodecode:templates/admin/integrations/form.html',
                        request_method='GET',
                        route_name=route_name)
        config.add_view('rhodecode.integrations.views.RepoGroupIntegrationsView',
                        attr='settings_post',
                        renderer='rhodecode:templates/admin/integrations/form.html',
                        request_method='POST',
                        route_name=route_name)


    # repo integrations
    config.add_route('repo_integrations_home',
                     add_route_requirements(
                        '{repo_name}/settings/integrations',
                        URL_NAME_REQUIREMENTS
                     ),
                     custom_predicates=(valid_repo,))
    config.add_route('repo_integrations_list',
                     add_route_requirements(
                        '{repo_name}/settings/integrations/{integration}',
                        URL_NAME_REQUIREMENTS
                     ),
                     custom_predicates=(valid_repo, valid_integration))
    for route_name in ['repo_integrations_home', 'repo_integrations_list']:
        config.add_view('rhodecode.integrations.views.RepoIntegrationsView',
                        attr='index',
                        request_method='GET',
                        renderer='rhodecode:templates/admin/integrations/list.html',
                        route_name=route_name)

    config.add_route('repo_integrations_new',
                     add_route_requirements(
                        '{repo_name}/settings/integrations/new',
                        URL_NAME_REQUIREMENTS
                     ),
                     custom_predicates=(valid_repo,))
    config.add_view('rhodecode.integrations.views.RepoIntegrationsView',
                    attr='new_integration',
                    renderer='rhodecode:templates/admin/integrations/new.html',
                    request_method='GET',
                    route_name='repo_integrations_new')

    config.add_route('repo_integrations_create',
                     add_route_requirements(
                        '{repo_name}/settings/integrations/{integration}/new',
                        URL_NAME_REQUIREMENTS
                     ),
                     custom_predicates=(valid_repo, valid_integration))
    config.add_route('repo_integrations_edit',
                     add_route_requirements(
                        '{repo_name}/settings/integrations/{integration}/{integration_id}',
                        URL_NAME_REQUIREMENTS
                     ),
                     custom_predicates=(valid_repo, valid_integration))
    for route_name in ['repo_integrations_edit', 'repo_integrations_create']:
        config.add_view('rhodecode.integrations.views.RepoIntegrationsView',
                        attr='settings_get',
                        renderer='rhodecode:templates/admin/integrations/form.html',
                        request_method='GET',
                        route_name=route_name)
        config.add_view('rhodecode.integrations.views.RepoIntegrationsView',
                        attr='settings_post',
                        renderer='rhodecode:templates/admin/integrations/form.html',
                        request_method='POST',
                        route_name=route_name)


def valid_repo(info, request):
    repo = Repository.get_by_repo_name(info['match']['repo_name'])
    if repo:
        return True


def valid_repo_group(info, request):
    repo_group = RepoGroup.get_by_group_name(info['match']['repo_group_name'])
    if repo_group:
        return True
    return False


def valid_integration(info, request):
    integration_type = info['match']['integration']
    integration_id = info['match'].get('integration_id')
    repo_name = info['match'].get('repo_name')
    repo_group_name = info['match'].get('repo_group_name')

    if integration_type not in integration_type_registry:
        return False

    repo, repo_group = None, None
    if repo_name:
        repo = Repository.get_by_repo_name(repo_name)
        if not repo:
            return False

    if repo_group_name:
        repo_group = RepoGroup.get_by_group_name(repo_group_name)
        if not repo_group:
            return False

    if repo_name and repo_group:
        raise Exception('Either repo or repo_group can be set, not both')


    if integration_id:
        integration = Integration.get(integration_id)
        if not integration:
            return False
        if integration.integration_type != integration_type:
            return False
        if repo and repo.repo_id != integration.repo_id:
            return False
        if repo_group and repo_group.group_id != integration.repo_group_id:
            return False

    return True
