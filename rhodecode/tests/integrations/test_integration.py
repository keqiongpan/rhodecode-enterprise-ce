# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
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


class TestDeleteScopesDeletesIntegrations(object):
    def test_delete_repo_with_integration_deletes_integration(
            self, repo_integration_stub):

        Session().delete(repo_integration_stub.repo)
        Session().commit()
        Session().expire_all()
        integration = Integration.get(repo_integration_stub.integration_id)
        assert integration is None

    def test_delete_repo_group_with_integration_deletes_integration(
            self, repogroup_integration_stub):

        Session().delete(repogroup_integration_stub.repo_group)
        Session().commit()
        Session().expire_all()
        integration = Integration.get(repogroup_integration_stub.integration_id)
        assert integration is None


count = 1


def counter():
    global count
    val = count
    count += 1
    return '{}_{}'.format(val, time.time())


@pytest.fixture()
def integration_repos(request, StubIntegrationType, stub_integration_settings):
    """
    Create repositories and integrations for testing, and destroy them after

    Structure:
        root_repo
        parent_group/
            parent_repo
            child_group/
                child_repo
        other_group/
            other_repo
    """
    fixture = Fixture()

    parent_group_id = 'int_test_parent_group_{}'.format(counter())
    parent_group = fixture.create_repo_group(parent_group_id)

    other_group_id = 'int_test_other_group_{}'.format(counter())
    other_group = fixture.create_repo_group(other_group_id)

    child_group_id = (
        parent_group_id + '/' + 'int_test_child_group_{}'.format(counter()))
    child_group = fixture.create_repo_group(child_group_id)

    parent_repo_id = 'int_test_parent_repo_{}'.format(counter())
    parent_repo = fixture.create_repo(parent_repo_id, repo_group=parent_group)

    child_repo_id = 'int_test_child_repo_{}'.format(counter())
    child_repo = fixture.create_repo(child_repo_id, repo_group=child_group)

    other_repo_id = 'int_test_other_repo_{}'.format(counter())
    other_repo = fixture.create_repo(other_repo_id, repo_group=other_group)

    root_repo_id = 'int_test_repo_root_{}'.format(counter())
    root_repo = fixture.create_repo(root_repo_id)

    integrations = {}
    for name, repo, repo_group, child_repos_only in [
            ('global', None, None, None),
            ('root_repos', None, None, True),
            ('parent_repo', parent_repo, None, None),
            ('child_repo', child_repo, None, None),
            ('other_repo', other_repo, None, None),
            ('root_repo', root_repo, None, None),
            ('parent_group', None, parent_group, True),
            ('parent_group_recursive', None, parent_group, False),
            ('child_group', None, child_group, True),
            ('child_group_recursive', None, child_group, False),
            ('other_group', None, other_group, True),
            ('other_group_recursive', None, other_group, False),
        ]:
        integrations[name] = IntegrationModel().create(
            StubIntegrationType, settings=stub_integration_settings,
            enabled=True, name='test %s integration' % name,
            repo=repo, repo_group=repo_group, child_repos_only=child_repos_only)

    Session().commit()

    def _cleanup():
        for integration in integrations.values():
            Session.delete(integration)

        fixture.destroy_repo(root_repo)
        fixture.destroy_repo(child_repo)
        fixture.destroy_repo(parent_repo)
        fixture.destroy_repo(other_repo)
        fixture.destroy_repo_group(child_group)
        fixture.destroy_repo_group(parent_group)
        fixture.destroy_repo_group(other_group)

    request.addfinalizer(_cleanup)

    return {
        'integrations': integrations,
        'repos': {
            'root_repo': root_repo,
            'other_repo': other_repo,
            'parent_repo': parent_repo,
            'child_repo': child_repo,
        }
    }


def test_enabled_integration_repo_scopes(integration_repos):
    integrations = integration_repos['integrations']
    repos = integration_repos['repos']

    triggered_integrations = IntegrationModel().get_for_event(
        events.RepoEvent(repos['root_repo']))

    assert triggered_integrations == [
        integrations['global'],
        integrations['root_repos'],
        integrations['root_repo'],
    ]

    triggered_integrations = IntegrationModel().get_for_event(
        events.RepoEvent(repos['other_repo']))

    assert triggered_integrations == [
        integrations['global'],
        integrations['other_group'],
        integrations['other_group_recursive'],
        integrations['other_repo'],
    ]

    triggered_integrations = IntegrationModel().get_for_event(
        events.RepoEvent(repos['parent_repo']))

    assert triggered_integrations == [
        integrations['global'],
        integrations['parent_group'],
        integrations['parent_group_recursive'],
        integrations['parent_repo'],
    ]

    triggered_integrations = IntegrationModel().get_for_event(
        events.RepoEvent(repos['child_repo']))

    assert triggered_integrations == [
        integrations['global'],
        integrations['child_group'],
        integrations['parent_group_recursive'],
        integrations['child_group_recursive'],
        integrations['child_repo'],
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
        events.RepoEvent(repos['parent_repo']))

    assert triggered_integrations == []

    triggered_integrations = IntegrationModel().get_for_event(
        events.RepoEvent(repos['child_repo']))

    assert triggered_integrations == []

    triggered_integrations = IntegrationModel().get_for_event(
        events.RepoEvent(repos['other_repo']))

    assert triggered_integrations == []


def test_enabled_non_repo_integrations(integration_repos):
    integrations = integration_repos['integrations']

    triggered_integrations = IntegrationModel().get_for_event(
        events.UserPreCreate({}))

    assert triggered_integrations == [integrations['global']]
