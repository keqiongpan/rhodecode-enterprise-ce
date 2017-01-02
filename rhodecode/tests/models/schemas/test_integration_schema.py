# -*- coding: utf-8 -*-

# Copyright (C) 2016-2017 RhodeCode GmbH
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

import colander
import pytest

from rhodecode.integrations import integration_type_registry
from rhodecode.integrations.types.base import IntegrationTypeBase
from rhodecode.model.validation_schema.schemas.integration_schema import (
    make_integration_schema
)


@pytest.mark.usefixtures('app', 'autologin_user')
class TestIntegrationSchema(object):

    def test_deserialize_integration_schema_perms(
            self, backend_random, test_repo_group, StubIntegrationType):

        repo = backend_random.repo
        repo_group = test_repo_group

        empty_perms_dict = {
            'global': [],
            'repositories': {},
            'repositories_groups': {},
        }

        perms_tests = [
            (
                'repo:%s' % repo.repo_name,
                {
                    'child_repos_only': None,
                    'repo_group': None,
                    'repo': repo,
                },
                [
                    ({},  False),
                    ({'global': ['hg.admin']},  True),
                    ({'global': []},  False),
                    ({'repositories': {repo.repo_name: 'repository.admin'}}, True),
                    ({'repositories': {repo.repo_name: 'repository.read'}}, False),
                    ({'repositories': {repo.repo_name: 'repository.write'}}, False),
                    ({'repositories': {repo.repo_name: 'repository.none'}}, False),
                ]
            ),
            (
                'repogroup:%s' % repo_group.group_name,
                {
                    'repo': None,
                    'repo_group': repo_group,
                    'child_repos_only': True,
                },
                [
                    ({},  False),
                    ({'global': ['hg.admin']},  True),
                    ({'global': []},  False),
                    ({'repositories_groups':
                        {repo_group.group_name: 'group.admin'}}, True),
                    ({'repositories_groups':
                        {repo_group.group_name: 'group.read'}}, False),
                    ({'repositories_groups':
                        {repo_group.group_name: 'group.write'}}, False),
                    ({'repositories_groups':
                        {repo_group.group_name: 'group.none'}}, False),
                ]
            ),
            (
                'repogroup-recursive:%s' % repo_group.group_name,
                {
                    'repo': None,
                    'repo_group': repo_group,
                    'child_repos_only': False,
                },
                [
                    ({},  False),
                    ({'global': ['hg.admin']},  True),
                    ({'global': []},  False),
                    ({'repositories_groups':
                        {repo_group.group_name: 'group.admin'}}, True),
                    ({'repositories_groups':
                        {repo_group.group_name: 'group.read'}}, False),
                    ({'repositories_groups':
                        {repo_group.group_name: 'group.write'}}, False),
                    ({'repositories_groups':
                        {repo_group.group_name: 'group.none'}}, False),
                ]
            ),
            (
                'global',
                {
                    'repo': None,
                    'repo_group': None,
                    'child_repos_only': False,
                }, [
                    ({},  False),
                    ({'global': ['hg.admin']},  True),
                    ({'global': []},  False),
                ]
            ),
            (
                'root-repos',
                {
                    'repo': None,
                    'repo_group': None,
                    'child_repos_only': True,
                }, [
                    ({},  False),
                    ({'global': ['hg.admin']},  True),
                    ({'global': []},  False),
                ]
            ),
        ]

        for scope_input, scope_output, perms_allowed in perms_tests:
            for perms_update, allowed in perms_allowed:
                perms = dict(empty_perms_dict, **perms_update)

                schema = make_integration_schema(
                    IntegrationType=StubIntegrationType
                ).bind(permissions=perms)

                input_data = {
                    'options': {
                        'enabled': 'true',
                        'scope': scope_input,
                        'name': 'test integration',
                    },
                    'settings': {
                        'test_string_field': 'stringy',
                        'test_int_field': '100',
                    }
                }

                if not allowed:
                    with pytest.raises(colander.Invalid):
                        schema.deserialize(input_data)
                else:
                    assert schema.deserialize(input_data) == {
                        'options': {
                            'enabled': True,
                            'scope': scope_output,
                            'name': 'test integration',
                        },
                        'settings': {
                            'test_string_field': 'stringy',
                            'test_int_field': 100,
                        }
                    }

