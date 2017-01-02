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

import os

import deform
import colander

from rhodecode.translation import _
from rhodecode.model.db import Repository, RepoGroup
from rhodecode.model.validation_schema import validators, preparers


def integration_scope_choices(permissions):
    """
    Return list of (value, label) choices for integration scopes depending on
    the permissions
    """
    result = [('', _('Pick a scope:'))]
    if 'hg.admin' in permissions['global']:
        result.extend([
           ('global', _('Global (all repositories)')),
           ('root-repos', _('Top level repositories only')),
        ])

    repo_choices = [
        ('repo:%s' % repo_name, '/' + repo_name)
        for repo_name, repo_perm
        in permissions['repositories'].items()
        if repo_perm == 'repository.admin'
    ]
    repogroup_choices = [
        ('repogroup:%s' % repo_group_name, '/' + repo_group_name + '/ (child repos only)')
        for repo_group_name, repo_group_perm
        in permissions['repositories_groups'].items()
        if repo_group_perm == 'group.admin'
    ]
    repogroup_recursive_choices = [
        ('repogroup-recursive:%s' % repo_group_name, '/' + repo_group_name + '/ (recursive)')
        for repo_group_name, repo_group_perm
        in permissions['repositories_groups'].items()
        if repo_group_perm == 'group.admin'
    ]
    result.extend(
        sorted(repogroup_recursive_choices + repogroup_choices + repo_choices,
            key=lambda (choice, label): choice.split(':', 1)[1]
        )
    )
    return result


@colander.deferred
def deferred_integration_scopes_validator(node, kw):
    perms = kw.get('permissions')
    def _scope_validator(_node, scope):
        is_super_admin = 'hg.admin' in perms['global']

        if scope.get('repo'):
            if (is_super_admin or perms['repositories'].get(
                scope['repo'].repo_name) == 'repository.admin'):
                return True
            msg = _('Only repo admins can create integrations')
            raise colander.Invalid(_node, msg)
        elif scope.get('repo_group'):
            if (is_super_admin or perms['repositories_groups'].get(
                scope['repo_group'].group_name) == 'group.admin'):
                return True

            msg = _('Only repogroup admins can create integrations')
            raise colander.Invalid(_node, msg)
        else:
            if is_super_admin:
                return True
            msg = _('Only superadmins can create global integrations')
            raise colander.Invalid(_node, msg)

    return _scope_validator


@colander.deferred
def deferred_integration_scopes_widget(node, kw):
    if kw.get('no_scope'):
        return deform.widget.TextInputWidget(readonly=True)

    choices = integration_scope_choices(kw.get('permissions'))
    widget = deform.widget.Select2Widget(values=choices)
    return widget


class IntegrationScopeType(colander.SchemaType):
    def serialize(self, node, appstruct):
        if appstruct is colander.null:
            return colander.null

        if appstruct.get('repo'):
            return 'repo:%s' % appstruct['repo'].repo_name
        elif appstruct.get('repo_group'):
            if appstruct.get('child_repos_only'):
                return 'repogroup:%s' % appstruct['repo_group'].group_name
            else:
                return 'repogroup-recursive:%s' % (
                    appstruct['repo_group'].group_name)
        else:
            if appstruct.get('child_repos_only'):
                return 'root-repos'
            else:
                return 'global'

        raise colander.Invalid(node, '%r is not a valid scope' % appstruct)

    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return colander.null

        if cstruct.startswith('repo:'):
            repo = Repository.get_by_repo_name(cstruct.split(':')[1])
            if repo:
                return {
                    'repo': repo,
                    'repo_group': None,
                    'child_repos_only': None,
                }
        elif cstruct.startswith('repogroup-recursive:'):
            repo_group = RepoGroup.get_by_group_name(cstruct.split(':')[1])
            if repo_group:
                return {
                    'repo': None,
                    'repo_group': repo_group,
                    'child_repos_only': False
                }
        elif cstruct.startswith('repogroup:'):
            repo_group = RepoGroup.get_by_group_name(cstruct.split(':')[1])
            if repo_group:
                return {
                    'repo': None,
                    'repo_group': repo_group,
                    'child_repos_only': True
                }
        elif cstruct == 'global':
            return {
                'repo': None,
                'repo_group': None,
                'child_repos_only': False
            }
        elif cstruct == 'root-repos':
            return {
                'repo': None,
                'repo_group': None,
                'child_repos_only': True
            }

        raise colander.Invalid(node, '%r is not a valid scope' % cstruct)


class IntegrationOptionsSchemaBase(colander.MappingSchema):

    name = colander.SchemaNode(
        colander.String(),
        description=_('Short name for this integration.'),
        missing=colander.required,
        title=_('Integration name'),
    )

    scope = colander.SchemaNode(
        IntegrationScopeType(),
        description=_(
            'Scope of the integration. Recursive means the integration '
            ' runs on all repos of that group and children recursively.'),
        title=_('Integration scope'),
        validator=deferred_integration_scopes_validator,
        widget=deferred_integration_scopes_widget,
        missing=colander.required,
    )

    enabled = colander.SchemaNode(
        colander.Bool(),
        default=True,
        description=_('Enable or disable this integration.'),
        missing=False,
        title=_('Enabled'),
    )



def make_integration_schema(IntegrationType, settings=None):
    """
    Return a colander schema for an integration type

    :param IntegrationType: the integration type class
    :param settings: existing integration settings dict (optional)
    """

    settings = settings or {}
    settings_schema = IntegrationType(settings=settings).settings_schema()

    class IntegrationSchema(colander.Schema):
        options = IntegrationOptionsSchemaBase()

    schema = IntegrationSchema()
    schema['options'].title = _('General integration options')

    settings_schema.name = 'settings'
    settings_schema.title = _('{integration_type} settings').format(
        integration_type=IntegrationType.display_name)
    schema.add(settings_schema)

    return schema


