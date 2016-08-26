# -*- coding: utf-8 -*-

# Copyright (C) 2010-2016  RhodeCode GmbH
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

import time
import pytest

from rhodecode import events
from rhodecode.tests.fixture import Fixture
from rhodecode.model.db import Session, Integration
from rhodecode.model.integration import IntegrationModel
from rhodecode.integrations.types.base import IntegrationTypeBase


class TestDeleteScopesDeletesIntegrations(object):
    def test_delete_repo_with_integration_deletes_integration(self,
        repo_integration_stub):
        Session().delete(repo_integration_stub.repo)
        Session().commit()
        Session().expire_all()
        integration = Integration.get(repo_integration_stub.integration_id)
        assert integration is None


    def test_delete_repo_group_with_integration_deletes_integration(self,
        repogroup_integration_stub):
        Session().delete(repogroup_integration_stub.repo_group)
        Session().commit()
        Session().expire_all()
        integration = Integration.get(repogroup_integration_stub.integration_id)
        assert integration is None


@pytest.fixture
def integration_repos(request, StubIntegrationType, stub_integration_settings):
    """
    Create repositories and integrations for testing, and destroy them after
    """
    fixture = Fixture()

    repo_group_1_id = 'int_test_repo_group_1_%s' % time.time()
    repo_group_1 = fixture.create_repo_group(repo_group_1_id)
    repo_group_2_id = 'int_test_repo_group_2_%s' % time.time()
    repo_group_2 = fixture.create_repo_group(repo_group_2_id)

    repo_1_id = 'int_test_repo_1_%s' % time.time()
    repo_1 = fixture.create_repo(repo_1_id, repo_group=repo_group_1)
    repo_2_id = 'int_test_repo_2_%s' % time.time()
    repo_2 = fixture.create_repo(repo_2_id, repo_group=repo_group_2)

    root_repo_id = 'int_test_repo_root_%s' % time.time()
    root_repo = fixture.create_repo(root_repo_id)

    integration_global = IntegrationModel().create(
        StubIntegrationType, settings=stub_integration_settings,
        enabled=True, name='test global integration', scope='global')
    integration_root_repos = IntegrationModel().create(
        StubIntegrationType, settings=stub_integration_settings,
        enabled=True, name='test root repos integration', scope='root_repos')
    integration_repo_1 = IntegrationModel().create(
        StubIntegrationType, settings=stub_integration_settings,
        enabled=True, name='test repo 1 integration', scope=repo_1)
    integration_repo_group_1 = IntegrationModel().create(
        StubIntegrationType, settings=stub_integration_settings,
        enabled=True, name='test repo group 1 integration', scope=repo_group_1)
    integration_repo_2 = IntegrationModel().create(
        StubIntegrationType, settings=stub_integration_settings,
        enabled=True, name='test repo 2 integration', scope=repo_2)
    integration_repo_group_2 = IntegrationModel().create(
        StubIntegrationType, settings=stub_integration_settings,
        enabled=True, name='test repo group 2 integration', scope=repo_group_2)

    Session().commit()

    def _cleanup():
        Session().delete(integration_global)
        Session().delete(integration_root_repos)
        Session().delete(integration_repo_1)
        Session().delete(integration_repo_group_1)
        Session().delete(integration_repo_2)
        Session().delete(integration_repo_group_2)
        fixture.destroy_repo(root_repo)
        fixture.destroy_repo(repo_1)
        fixture.destroy_repo(repo_2)
        fixture.destroy_repo_group(repo_group_1)
        fixture.destroy_repo_group(repo_group_2)

    request.addfinalizer(_cleanup)

    return {
        'repos': {
            'repo_1': repo_1,
            'repo_2': repo_2,
            'root_repo': root_repo,
        },
        'repo_groups': {
            'repo_group_1': repo_group_1,
            'repo_group_2': repo_group_2,
        },
        'integrations': {
            'global': integration_global,
            'root_repos': integration_root_repos,
            'repo_1': integration_repo_1,
            'repo_2': integration_repo_2,
            'repo_group_1': integration_repo_group_1,
            'repo_group_2': integration_repo_group_2,
        }
    }


def test_enabled_integration_repo_scopes(integration_repos):
    integrations = integration_repos['integrations']
    repos = integration_repos['repos']

    triggered_integrations = IntegrationModel().get_for_event(
        events.RepoEvent(repos['root_repo']))

    assert triggered_integrations == [
        integrations['global'],
        integrations['root_repos']
    ]


    triggered_integrations = IntegrationModel().get_for_event(
        events.RepoEvent(repos['repo_1']))

    assert triggered_integrations == [
        integrations['global'],
        integrations['repo_1'],
        integrations['repo_group_1']
    ]


    triggered_integrations = IntegrationModel().get_for_event(
        events.RepoEvent(repos['repo_2']))

    assert triggered_integrations == [
        integrations['global'],
        integrations['repo_2'],
        integrations['repo_group_2'],
    ]


def test_disabled_integration_repo_scopes(integration_repos):
    integrations = integration_repos['integrations']
    repos = integration_repos['repos']

    for integration in integrations.values():
        integration.enabled = False
    Session().commit()

    triggered_integrations = IntegrationModel().get_for_event(
        events.RepoEvent(repos['root_repo']))

    assert triggered_integrations == []


    triggered_integrations = IntegrationModel().get_for_event(
        events.RepoEvent(repos['repo_1']))

    assert triggered_integrations == []


    triggered_integrations = IntegrationModel().get_for_event(
        events.RepoEvent(repos['repo_2']))

    assert triggered_integrations == []


def test_enabled_non_repo_integrations(integration_repos):
    integrations = integration_repos['integrations']

    triggered_integrations = IntegrationModel().get_for_event(
        events.UserPreCreate({}))

    assert triggered_integrations == [integrations['global']]
