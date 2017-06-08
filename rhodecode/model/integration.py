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


"""
Model for integrations
"""


import logging

from sqlalchemy import or_, and_

import rhodecode
from rhodecode import events
from rhodecode.lib.caching_query import FromCache
from rhodecode.model import BaseModel
from rhodecode.model.db import Integration, Repository, RepoGroup
from rhodecode.integrations import integration_type_registry

log = logging.getLogger(__name__)


class IntegrationModel(BaseModel):

    cls = Integration

    def __get_integration(self, integration):
        if isinstance(integration, Integration):
            return integration
        elif isinstance(integration, (int, long)):
            return self.sa.query(Integration).get(integration)
        else:
            if integration:
                raise Exception('integration must be int, long or Instance'
                                ' of Integration got %s' % type(integration))

    def create(self, IntegrationType, name, enabled, repo, repo_group,
        child_repos_only, settings):
        """ Create an IntegrationType integration """
        integration = Integration()
        integration.integration_type = IntegrationType.key
        self.sa.add(integration)
        self.update_integration(integration, name, enabled, repo, repo_group,
                                child_repos_only, settings)
        self.sa.commit()
        return integration

    def update_integration(self, integration, name, enabled, repo, repo_group,
        child_repos_only, settings):
        integration = self.__get_integration(integration)

        integration.repo = repo
        integration.repo_group = repo_group
        integration.child_repos_only = child_repos_only
        integration.name = name
        integration.enabled = enabled
        integration.settings = settings

        return integration

    def delete(self, integration):
        integration = self.__get_integration(integration)
        if integration:
            self.sa.delete(integration)
            return True
        return False

    def get_integration_handler(self, integration):
        TypeClass = integration_type_registry.get(integration.integration_type)
        if not TypeClass:
            log.error('No class could be found for integration type: {}'.format(
                integration.integration_type))
            return None

        return TypeClass(integration.settings)

    def send_event(self, integration, event):
        """ Send an event to an integration """
        handler = self.get_integration_handler(integration)
        if handler:
            log.debug(
                'events: sending event %s on integration %s using handler %s',
                event, integration, handler)
            handler.send_event(event)

    def get_integrations(self, scope, IntegrationType=None):
        """
        Return integrations for a scope, which must be one of:

        'all' - every integration, global/repogroup/repo
        'global' - global integrations only
        <Repository> instance - integrations for this repo only
        <RepoGroup> instance - integrations for this repogroup only
        """

        if isinstance(scope, Repository):
            query = self.sa.query(Integration).filter(
                Integration.repo==scope)
        elif isinstance(scope, RepoGroup):
            query = self.sa.query(Integration).filter(
                Integration.repo_group==scope)
        elif scope == 'global':
            # global integrations
            query = self.sa.query(Integration).filter(
                and_(Integration.repo_id==None, Integration.repo_group_id==None)
            )
        elif scope == 'root-repos':
            query = self.sa.query(Integration).filter(
                and_(Integration.repo_id==None,
                     Integration.repo_group_id==None,
                     Integration.child_repos_only==True)
            )
        elif scope == 'all':
            query = self.sa.query(Integration)
        else:
            raise Exception(
                "invalid `scope`, must be one of: "
                "['global', 'all', <Repository>, <RepoGroup>]")

        if IntegrationType is not None:
            query = query.filter(
                Integration.integration_type==IntegrationType.key)

        result = []
        for integration in query.all():
            IntType = integration_type_registry.get(integration.integration_type)
            result.append((IntType, integration))
        return result

    def get_for_event(self, event, cache=False):
        """
        Get integrations that match an event
        """
        query = self.sa.query(
            Integration
        ).filter(
            Integration.enabled==True
        )

        global_integrations_filter = and_(
            Integration.repo_id==None,
            Integration.repo_group_id==None,
            Integration.child_repos_only==False,
        )

        if isinstance(event, events.RepoEvent):
            root_repos_integrations_filter = and_(
                Integration.repo_id==None,
                Integration.repo_group_id==None,
                Integration.child_repos_only==True,
            )

            clauses = [
                global_integrations_filter,
            ]

            # repo integrations
            if event.repo.repo_id: # pre create events dont have a repo_id yet
                clauses.append(
                    Integration.repo_id==event.repo.repo_id
                )

            if event.repo.group:
                clauses.append(
                    and_(
                        Integration.repo_group_id==event.repo.group.group_id,
                        Integration.child_repos_only==True
                    )
                )
                # repo group cascade to kids
                clauses.append(
                    and_(
                        Integration.repo_group_id.in_(
                            [group.group_id for group in
                            event.repo.groups_with_parents]
                        ),
                        Integration.child_repos_only==False
                    )
                )


            if not event.repo.group: # root repo
                clauses.append(root_repos_integrations_filter)

            query = query.filter(or_(*clauses))

            if cache:
                cache_key = "get_enabled_repo_integrations_%i" % event.repo.repo_id
                query = query.options(
                    FromCache("sql_cache_short", cache_key))
        else: # only global integrations
            query = query.filter(global_integrations_filter)
            if cache:
                query = query.options(
                    FromCache("sql_cache_short", "get_enabled_global_integrations"))

        result = query.all()
        return result