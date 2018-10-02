# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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

import pytest

from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.model.db import Integration
from rhodecode.model.meta import Session
from rhodecode.integrations import integration_type_registry


def route_path(name, **kwargs):
    return {
        'home': '/',
    }[name].format(**kwargs)


def _post_integration_test_helper(app, url, csrf_token, repo, repo_group,
                                  admin_view):
    """
    Posts form data to create integration at the url given then deletes it and
    checks if the redirect url is correct.
    """
    repo_name = repo.repo_name
    repo_group_name = repo_group.group_name
    app.post(url, params={}, status=403)  # missing csrf check
    response = app.post(url, params={'csrf_token': csrf_token})
    assert response.status_code == 200
    response.mustcontain('Errors exist')

    scopes_destinations = [
        ('global',
                ADMIN_PREFIX + '/integrations'),
        ('root-repos',
                ADMIN_PREFIX + '/integrations'),
        ('repo:%s' % repo_name,
                '/%s/settings/integrations' % repo_name),
        ('repogroup:%s' % repo_group_name,
                '/%s/_settings/integrations' % repo_group_name),
        ('repogroup-recursive:%s' % repo_group_name,
                '/%s/_settings/integrations' % repo_group_name),
    ]

    for scope, destination in scopes_destinations:
        if admin_view:
            destination = ADMIN_PREFIX + '/integrations'

        form_data = [
            ('csrf_token', csrf_token),
            ('__start__', 'options:mapping'),
            ('name', 'test integration'),
            ('scope', scope),
            ('enabled', 'true'),
            ('__end__', 'options:mapping'),
            ('__start__', 'settings:mapping'),
            ('test_int_field', '34'),
            ('test_string_field', ''), # empty value on purpose as it's required
            ('__end__', 'settings:mapping'),
        ]
        errors_response = app.post(url, form_data)
        assert 'Errors exist' in errors_response.body

        form_data[-2] = ('test_string_field', 'data!')
        assert Session().query(Integration).count() == 0
        created_response = app.post(url, form_data)
        assert Session().query(Integration).count() == 1

        delete_response = app.post(
            created_response.location,
            params={'csrf_token': csrf_token, 'delete': 'delete'})

        assert Session().query(Integration).count() == 0
        assert delete_response.location.endswith(destination)



@pytest.mark.usefixtures('app', 'autologin_user')
class TestIntegrationsView(object):
    pass


class TestGlobalIntegrationsView(TestIntegrationsView):
    def test_index_no_integrations(self):
        url = ADMIN_PREFIX + '/integrations'
        response = self.app.get(url)

        assert response.status_code == 200
        response.mustcontain('exist yet')

    def test_index_with_integrations(self, global_integration_stub):
        url = ADMIN_PREFIX + '/integrations'
        response = self.app.get(url)

        assert response.status_code == 200
        response.mustcontain(no=['exist yet'])
        response.mustcontain(global_integration_stub.name)

    @pytest.mark.parametrize(
        'IntegrationType', integration_type_registry.values())
    def test_new_integration_page(self, IntegrationType):
        url = ADMIN_PREFIX + '/integrations/new'

        response = self.app.get(url, status=200)
        if not IntegrationType.is_dummy:
            url = (ADMIN_PREFIX + '/integrations/{integration}/new').format(
                    integration=IntegrationType.key)
            response.mustcontain(url)

    @pytest.mark.parametrize(
        'IntegrationType', integration_type_registry.values())
    def test_get_create_integration_page(self, IntegrationType):
        url = ADMIN_PREFIX + '/integrations/{integration_key}/new'.format(
            integration_key=IntegrationType.key)
        if IntegrationType.is_dummy:
            self.app.get(url, status=404)
        else:
            response = self.app.get(url, status=200)
            response.mustcontain(IntegrationType.display_name)

    def test_post_integration_page(self, StubIntegrationType, csrf_token,
                                   test_repo_group, backend_random):
        url = ADMIN_PREFIX + '/integrations/{integration_key}/new'.format(
            integration_key=StubIntegrationType.key)

        _post_integration_test_helper(
            self.app, url, csrf_token, admin_view=True,
            repo=backend_random.repo, repo_group=test_repo_group)


class TestRepoIntegrationsView(TestIntegrationsView):
    def test_index_no_integrations(self, backend_random):
        url = '/{repo_name}/settings/integrations'.format(
            repo_name=backend_random.repo.repo_name)
        response = self.app.get(url)

        assert response.status_code == 200
        response.mustcontain('exist yet')

    def test_index_with_integrations(self, repo_integration_stub):
        url = '/{repo_name}/settings/integrations'.format(
            repo_name=repo_integration_stub.repo.repo_name)
        stub_name = repo_integration_stub.name

        response = self.app.get(url)

        assert response.status_code == 200
        response.mustcontain(stub_name)
        response.mustcontain(no=['exist yet'])

    @pytest.mark.parametrize(
        'IntegrationType', integration_type_registry.values())
    def test_new_integration_page(self, backend_random, IntegrationType):
        repo_name = backend_random.repo.repo_name
        url = '/{repo_name}/settings/integrations/new'.format(
            repo_name=repo_name)

        response = self.app.get(url, status=200)

        url = '/{repo_name}/settings/integrations/{integration}/new'.format(
                repo_name=repo_name,
                integration=IntegrationType.key)
        if not IntegrationType.is_dummy:
            response.mustcontain(url)

    @pytest.mark.parametrize(
        'IntegrationType', integration_type_registry.values())
    def test_get_create_integration_page(self, backend_random, IntegrationType):
        repo_name = backend_random.repo.repo_name
        url = '/{repo_name}/settings/integrations/{integration_key}/new'.format(
            repo_name=repo_name, integration_key=IntegrationType.key)
        if IntegrationType.is_dummy:
            self.app.get(url, status=404)
        else:
            response = self.app.get(url, status=200)
            response.mustcontain(IntegrationType.display_name)

    def test_post_integration_page(self, backend_random, test_repo_group,
                                   StubIntegrationType, csrf_token):
        repo_name = backend_random.repo.repo_name
        url = '/{repo_name}/settings/integrations/{integration_key}/new'.format(
            repo_name=repo_name, integration_key=StubIntegrationType.key)

        _post_integration_test_helper(
            self.app, url, csrf_token, admin_view=False,
            repo=backend_random.repo, repo_group=test_repo_group)


class TestRepoGroupIntegrationsView(TestIntegrationsView):
    def test_index_no_integrations(self, test_repo_group):
        url = '/{repo_group_name}/_settings/integrations'.format(
            repo_group_name=test_repo_group.group_name)
        response = self.app.get(url)

        assert response.status_code == 200
        response.mustcontain('exist yet')

    def test_index_with_integrations(
            self, test_repo_group, repogroup_integration_stub):

        url = '/{repo_group_name}/_settings/integrations'.format(
            repo_group_name=test_repo_group.group_name)

        stub_name = repogroup_integration_stub.name
        response = self.app.get(url)

        assert response.status_code == 200
        response.mustcontain(no=['exist yet'])
        response.mustcontain(stub_name)

    def test_new_integration_page(self, test_repo_group):
        repo_group_name = test_repo_group.group_name
        url = '/{repo_group_name}/_settings/integrations/new'.format(
            repo_group_name=test_repo_group.group_name)

        response = self.app.get(url)

        assert response.status_code == 200

        for integration_key, integration_obj in integration_type_registry.items():
            if not integration_obj.is_dummy:
                nurl = (
                    '/{repo_group_name}/_settings/integrations/{integration}/new').format(
                    repo_group_name=repo_group_name,
                    integration=integration_key)
                response.mustcontain(nurl)

    @pytest.mark.parametrize(
        'IntegrationType', integration_type_registry.values())
    def test_get_create_integration_page(
            self, test_repo_group, IntegrationType):

        repo_group_name = test_repo_group.group_name
        url = ('/{repo_group_name}/_settings/integrations/{integration_key}/new'
               ).format(repo_group_name=repo_group_name,
                        integration_key=IntegrationType.key)

        if not IntegrationType.is_dummy:
            response = self.app.get(url, status=200)
            response.mustcontain(IntegrationType.display_name)
        else:
            self.app.get(url, status=404)

    def test_post_integration_page(self, test_repo_group, backend_random,
                                   StubIntegrationType, csrf_token):

        repo_group_name = test_repo_group.group_name
        url = ('/{repo_group_name}/_settings/integrations/{integration_key}/new'
               ).format(repo_group_name=repo_group_name,
                        integration_key=StubIntegrationType.key)

        _post_integration_test_helper(
            self.app, url, csrf_token, admin_view=False,
            repo=backend_random.repo, repo_group=test_repo_group)
