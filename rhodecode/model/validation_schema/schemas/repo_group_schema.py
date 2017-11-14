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
import deform.widget

from rhodecode.translation import _
from rhodecode.model.validation_schema import validators, preparers, types


def get_group_and_repo(repo_name):
    from rhodecode.model.repo_group import RepoGroupModel
    return RepoGroupModel()._get_group_name_and_parent(
        repo_name, get_object=True)


def get_repo_group(repo_group_id):
    from rhodecode.model.repo_group import RepoGroup
    return RepoGroup.get(repo_group_id), RepoGroup.CHOICES_SEPARATOR


@colander.deferred
def deferred_can_write_to_group_validator(node, kw):
    old_values = kw.get('old_values') or {}
    request_user = kw.get('user')

    def can_write_group_validator(node, value):
        from rhodecode.lib.auth import (
            HasPermissionAny, HasRepoGroupPermissionAny)
        from rhodecode.model.repo_group import RepoGroupModel

        messages = {
            'invalid_parent_repo_group':
                _(u"Parent repository group `{}` does not exist"),
            # permissions denied we expose as not existing, to prevent
            # resource discovery
            'permission_denied_parent_group':
                _(u"Parent repository group `{}` does not exist"),
            'permission_denied_root':
                _(u"You do not have the permission to store "
                  u"repository groups in the root location.")
        }

        value = value['repo_group_name']
        parent_group_name = value

        is_root_location = value is types.RootLocation

        # NOT initialized validators, we must call them
        can_create_repo_groups_at_root = HasPermissionAny(
            'hg.admin', 'hg.repogroup.create.true')

        if is_root_location:
            if can_create_repo_groups_at_root(user=request_user):
                # we can create repo group inside tool-level. No more checks
                # are required
                return
            else:
                raise colander.Invalid(node, messages['permission_denied_root'])

        # check if the parent repo group actually exists
        parent_group = None
        if parent_group_name:
            parent_group = RepoGroupModel().get_by_group_name(parent_group_name)
            if value and not parent_group:
                raise colander.Invalid(
                    node, messages['invalid_parent_repo_group'].format(
                        parent_group_name))

        # check if we have permissions to create new groups under
        # parent repo group
        # create repositories with write permission on group is set to true
        create_on_write = HasPermissionAny(
            'hg.create.write_on_repogroup.true')(user=request_user)

        group_admin = HasRepoGroupPermissionAny('group.admin')(
            parent_group_name, 'can write into group validator', user=request_user)
        group_write = HasRepoGroupPermissionAny('group.write')(
            parent_group_name, 'can write into group validator', user=request_user)

        # creation by write access is currently disabled. Needs thinking if
        # we want to allow this...
        forbidden = not (group_admin or (group_write and create_on_write and 0))

        if parent_group and forbidden:
            msg = messages['permission_denied_parent_group'].format(
                parent_group_name)
            raise colander.Invalid(node, msg)

    return can_write_group_validator


@colander.deferred
def deferred_repo_group_owner_validator(node, kw):

    def repo_owner_validator(node, value):
        from rhodecode.model.db import User
        existing = User.get_by_username(value)
        if not existing:
            msg = _(u'Repo group owner with id `{}` does not exists').format(
                value)
            raise colander.Invalid(node, msg)

    return repo_owner_validator


@colander.deferred
def deferred_unique_name_validator(node, kw):
    request_user = kw.get('user')
    old_values = kw.get('old_values') or {}

    def unique_name_validator(node, value):
        from rhodecode.model.db import Repository, RepoGroup
        name_changed = value != old_values.get('group_name')

        existing = Repository.get_by_repo_name(value)
        if name_changed and existing:
            msg = _(u'Repository with name `{}` already exists').format(value)
            raise colander.Invalid(node, msg)

        existing_group = RepoGroup.get_by_group_name(value)
        if name_changed and existing_group:
            msg = _(u'Repository group with name `{}` already exists').format(
                value)
            raise colander.Invalid(node, msg)
    return unique_name_validator


@colander.deferred
def deferred_repo_group_name_validator(node, kw):
    return validators.valid_name_validator


@colander.deferred
def deferred_repo_group_validator(node, kw):
    options = kw.get(
        'repo_group_repo_group_options')
    return colander.OneOf([x for x in options])


@colander.deferred
def deferred_repo_group_widget(node, kw):
    items = kw.get('repo_group_repo_group_items')
    return deform.widget.Select2Widget(values=items)


class GroupType(colander.Mapping):
    def _validate(self, node, value):
        try:
            return dict(repo_group_name=value)
        except Exception as e:
            raise colander.Invalid(
                node, '"${val}" is not a mapping type: ${err}'.format(
                    val=value, err=e))

    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return cstruct

        appstruct = super(GroupType, self).deserialize(node, cstruct)
        validated_name = appstruct['repo_group_name']

        # inject group based on once deserialized data
        (repo_group_name_without_group,
         parent_group_name,
         parent_group) = get_group_and_repo(validated_name)

        appstruct['repo_group_name_with_group'] = validated_name
        appstruct['repo_group_name_without_group'] = repo_group_name_without_group
        appstruct['repo_group_name'] = parent_group_name or types.RootLocation
        if parent_group:
            appstruct['repo_group_id'] = parent_group.group_id

        return appstruct


class GroupSchema(colander.SchemaNode):
    schema_type = GroupType
    validator = deferred_can_write_to_group_validator
    missing = colander.null


class RepoGroup(GroupSchema):
    repo_group_name = colander.SchemaNode(
        types.GroupNameType())
    repo_group_id = colander.SchemaNode(
        colander.String(), missing=None)
    repo_group_name_without_group = colander.SchemaNode(
        colander.String(), missing=None)


class RepoGroupAccessSchema(colander.MappingSchema):
    repo_group = RepoGroup()


class RepoGroupNameUniqueSchema(colander.MappingSchema):
    unique_repo_group_name = colander.SchemaNode(
        colander.String(),
        validator=deferred_unique_name_validator)


class RepoGroupSchema(colander.Schema):

    repo_group_name = colander.SchemaNode(
        types.GroupNameType(),
        validator=deferred_repo_group_name_validator)

    repo_group_owner = colander.SchemaNode(
        colander.String(),
        validator=deferred_repo_group_owner_validator)

    repo_group_description = colander.SchemaNode(
        colander.String(), missing='', widget=deform.widget.TextAreaWidget())

    repo_group_copy_permissions = colander.SchemaNode(
        types.StringBooleanType(),
        missing=False, widget=deform.widget.CheckboxWidget())

    repo_group_enable_locking = colander.SchemaNode(
        types.StringBooleanType(),
        missing=False, widget=deform.widget.CheckboxWidget())

    def deserialize(self, cstruct):
        """
        Custom deserialize that allows to chain validation, and verify
        permissions, and as last step uniqueness
        """

        appstruct = super(RepoGroupSchema, self).deserialize(cstruct)
        validated_name = appstruct['repo_group_name']

        # second pass to validate permissions to repo_group
        second = RepoGroupAccessSchema().bind(**self.bindings)
        appstruct_second = second.deserialize({'repo_group': validated_name})
        # save result
        appstruct['repo_group'] = appstruct_second['repo_group']

        # thirds to validate uniqueness
        third = RepoGroupNameUniqueSchema().bind(**self.bindings)
        third.deserialize({'unique_repo_group_name': validated_name})

        return appstruct


class RepoGroupSettingsSchema(RepoGroupSchema):
    repo_group = colander.SchemaNode(
        colander.Integer(),
        validator=deferred_repo_group_validator,
        widget=deferred_repo_group_widget,
        missing='')

    def deserialize(self, cstruct):
        """
        Custom deserialize that allows to chain validation, and verify
        permissions, and as last step uniqueness
        """

        # first pass, to validate given data
        appstruct = super(RepoGroupSchema, self).deserialize(cstruct)
        validated_name = appstruct['repo_group_name']

        # because of repoSchema adds repo-group as an ID, we inject it as
        # full name here because validators require it, it's unwrapped later
        # so it's safe to use and final name is going to be without group anyway

        group, separator = get_repo_group(appstruct['repo_group'])
        if group:
            validated_name = separator.join([group.group_name, validated_name])

        # second pass to validate permissions to repo_group
        second = RepoGroupAccessSchema().bind(**self.bindings)
        appstruct_second = second.deserialize({'repo_group': validated_name})
        # save result
        appstruct['repo_group'] = appstruct_second['repo_group']

        # thirds to validate uniqueness
        third = RepoGroupNameUniqueSchema().bind(**self.bindings)
        third.deserialize({'unique_repo_group_name': validated_name})

        return appstruct
