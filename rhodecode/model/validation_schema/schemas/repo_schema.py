# -*- coding: utf-8 -*-

# Copyright (C) 2016-2020 RhodeCode GmbH
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
from rhodecode.model.validation_schema.utils import convert_to_optgroup, username_converter
from rhodecode.model.validation_schema import validators, preparers, types

DEFAULT_LANDING_REF = 'rev:tip'
DEFAULT_BACKEND_LANDING_REF = {
    'hg': 'branch:default',
    'git': 'branch:master',
    'svn': 'rev:tip',
}


def get_group_and_repo(repo_name):
    from rhodecode.model.repo_group import RepoGroupModel
    return RepoGroupModel()._get_group_name_and_parent(
        repo_name, get_object=True)


def get_repo_group(repo_group_id):
    from rhodecode.model.repo_group import RepoGroup
    return RepoGroup.get(repo_group_id), RepoGroup.CHOICES_SEPARATOR


@colander.deferred
def deferred_repo_type_validator(node, kw):
    options = kw.get('repo_type_options', [])
    return colander.OneOf([x for x in options])


@colander.deferred
def deferred_repo_owner_validator(node, kw):

    def repo_owner_validator(node, value):
        from rhodecode.model.db import User
        value = username_converter(value)
        existing = User.get_by_username(value)
        if not existing:
            msg = _(u'Repo owner with id `{}` does not exists').format(value)
            raise colander.Invalid(node, msg)

    return repo_owner_validator


@colander.deferred
def deferred_landing_ref_validator(node, kw):
    options = kw.get(
        'repo_ref_options', [DEFAULT_LANDING_REF])
    return colander.OneOf([x for x in options])


@colander.deferred
def deferred_sync_uri_validator(node, kw):
    repo_type = kw.get('repo_type')
    validator = validators.CloneUriValidator(repo_type)
    return validator


@colander.deferred
def deferred_landing_ref_widget(node, kw):
    repo_type = kw.get('repo_type')
    default_opts = []
    if repo_type:
        default_opts.append(
            (DEFAULT_BACKEND_LANDING_REF[repo_type],
             DEFAULT_BACKEND_LANDING_REF[repo_type]))

    items = kw.get('repo_ref_items', default_opts)
    items = convert_to_optgroup(items)
    return deform.widget.Select2Widget(values=items)


@colander.deferred
def deferred_fork_of_validator(node, kw):
    old_values = kw.get('old_values') or {}

    def fork_of_validator(node, value):
        from rhodecode.model.db import Repository, RepoGroup
        existing = Repository.get_by_repo_name(value)
        if not existing:
            msg = _(u'Fork with id `{}` does not exists').format(value)
            raise colander.Invalid(node, msg)
        elif old_values['repo_name'] == existing.repo_name:
            msg = _(u'Cannot set fork of '
                    u'parameter of this repository to itself').format(value)
            raise colander.Invalid(node, msg)

    return fork_of_validator


@colander.deferred
def deferred_can_write_to_group_validator(node, kw):
    request_user = kw.get('user')
    old_values = kw.get('old_values') or {}

    def can_write_to_group_validator(node, value):
        """
        Checks if given repo path is writable by user. This includes checks if
        user is allowed to create repositories under root path or under
        repo group paths
        """

        from rhodecode.lib.auth import (
            HasPermissionAny, HasRepoGroupPermissionAny)
        from rhodecode.model.repo_group import RepoGroupModel

        messages = {
            'invalid_repo_group':
                _(u"Repository group `{}` does not exist"),
            # permissions denied we expose as not existing, to prevent
            # resource discovery
            'permission_denied':
                _(u"Repository group `{}` does not exist"),
            'permission_denied_root':
                _(u"You do not have the permission to store "
                  u"repositories in the root location.")
        }

        value = value['repo_group_name']

        is_root_location = value is types.RootLocation
        # NOT initialized validators, we must call them
        can_create_repos_at_root = HasPermissionAny('hg.admin', 'hg.create.repository')

        # if values is root location, we simply need to check if we can write
        # to root location !
        if is_root_location:

            if can_create_repos_at_root(user=request_user):
                # we can create repo group inside tool-level. No more checks
                # are required
                return
            else:
                old_name = old_values.get('repo_name')
                if old_name and old_name == old_values.get('submitted_repo_name'):
                    # since we didn't change the name, we can skip validation and
                    # allow current users without store-in-root permissions to update
                    return

                # "fake" node name as repo_name, otherwise we oddly report
                # the error as if it was coming form repo_group
                # however repo_group is empty when using root location.
                node.name = 'repo_name'
                raise colander.Invalid(node, messages['permission_denied_root'])

        # parent group not exists ? throw an error
        repo_group = RepoGroupModel().get_by_group_name(value)
        if value and not repo_group:
            raise colander.Invalid(
                node, messages['invalid_repo_group'].format(value))

        gr_name = repo_group.group_name

        # create repositories with write permission on group is set to true
        create_on_write = HasPermissionAny(
            'hg.create.write_on_repogroup.true')(user=request_user)

        group_admin = HasRepoGroupPermissionAny('group.admin')(
            gr_name, 'can write into group validator', user=request_user)
        group_write = HasRepoGroupPermissionAny('group.write')(
            gr_name, 'can write into group validator', user=request_user)

        forbidden = not (group_admin or (group_write and create_on_write))

        # TODO: handling of old values, and detecting no-change in path
        # to skip permission checks in such cases. This only needs to be
        # implemented if we use this schema in forms as well

        # gid = (old_data['repo_group'].get('group_id')
        #        if (old_data and 'repo_group' in old_data) else None)
        # value_changed = gid != safe_int(value)
        # new = not old_data

        # do check if we changed the value, there's a case that someone got
        # revoked write permissions to a repository, he still created, we
        # don't need to check permission if he didn't change the value of
        # groups in form box
        # if value_changed or new:
        #     # parent group need to be existing
        # TODO: ENDS HERE

        if repo_group and forbidden:
            msg = messages['permission_denied'].format(value)
            raise colander.Invalid(node, msg)

    return can_write_to_group_validator


@colander.deferred
def deferred_unique_name_validator(node, kw):
    request_user = kw.get('user')
    old_values = kw.get('old_values') or {}

    def unique_name_validator(node, value):
        from rhodecode.model.db import Repository, RepoGroup
        name_changed = value != old_values.get('repo_name')

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
def deferred_repo_name_validator(node, kw):
    def no_git_suffix_validator(node, value):
        if value.endswith('.git'):
            msg = _('Repository name cannot end with .git')
            raise colander.Invalid(node, msg)
    return colander.All(
        no_git_suffix_validator, validators.valid_name_validator)


@colander.deferred
def deferred_repo_group_validator(node, kw):
    options = kw.get(
        'repo_repo_group_options')
    return colander.OneOf([x for x in options])


@colander.deferred
def deferred_repo_group_widget(node, kw):
    items = kw.get('repo_repo_group_items')
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
        (repo_name_without_group,
         parent_group_name,
         parent_group) = get_group_and_repo(validated_name)

        appstruct['repo_name_with_group'] = validated_name
        appstruct['repo_name_without_group'] = repo_name_without_group
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
    repo_name_without_group = colander.SchemaNode(
        colander.String(), missing=None)


class RepoGroupAccessSchema(colander.MappingSchema):
    repo_group = RepoGroup()


class RepoNameUniqueSchema(colander.MappingSchema):
    unique_repo_name = colander.SchemaNode(
        colander.String(),
        validator=deferred_unique_name_validator)


class RepoSchema(colander.MappingSchema):

    repo_name = colander.SchemaNode(
        types.RepoNameType(),
        validator=deferred_repo_name_validator)

    repo_type = colander.SchemaNode(
        colander.String(),
        validator=deferred_repo_type_validator)

    repo_owner = colander.SchemaNode(
        colander.String(),
        validator=deferred_repo_owner_validator,
        widget=deform.widget.TextInputWidget())

    repo_description = colander.SchemaNode(
        colander.String(), missing='',
        widget=deform.widget.TextAreaWidget())

    repo_landing_commit_ref = colander.SchemaNode(
        colander.String(),
        validator=deferred_landing_ref_validator,
        preparers=[preparers.strip_preparer],
        missing=DEFAULT_LANDING_REF,
        widget=deferred_landing_ref_widget)

    repo_clone_uri = colander.SchemaNode(
        colander.String(),
        validator=deferred_sync_uri_validator,
        preparers=[preparers.strip_preparer],
        missing='')

    repo_push_uri = colander.SchemaNode(
        colander.String(),
        validator=deferred_sync_uri_validator,
        preparers=[preparers.strip_preparer],
        missing='')

    repo_fork_of = colander.SchemaNode(
        colander.String(),
        validator=deferred_fork_of_validator,
        missing=None)

    repo_private = colander.SchemaNode(
        types.StringBooleanType(),
        missing=False, widget=deform.widget.CheckboxWidget())
    repo_copy_permissions = colander.SchemaNode(
        types.StringBooleanType(),
        missing=False, widget=deform.widget.CheckboxWidget())
    repo_enable_statistics = colander.SchemaNode(
        types.StringBooleanType(),
        missing=False, widget=deform.widget.CheckboxWidget())
    repo_enable_downloads = colander.SchemaNode(
        types.StringBooleanType(),
        missing=False, widget=deform.widget.CheckboxWidget())
    repo_enable_locking = colander.SchemaNode(
        types.StringBooleanType(),
        missing=False, widget=deform.widget.CheckboxWidget())

    def deserialize(self, cstruct):
        """
        Custom deserialize that allows to chain validation, and verify
        permissions, and as last step uniqueness
        """

        # first pass, to validate given data
        appstruct = super(RepoSchema, self).deserialize(cstruct)
        validated_name = appstruct['repo_name']

        # second pass to validate permissions to repo_group
        if 'old_values' in self.bindings:
            # save current repo name for name change checks
            self.bindings['old_values']['submitted_repo_name'] = validated_name
        second = RepoGroupAccessSchema().bind(**self.bindings)
        appstruct_second = second.deserialize({'repo_group': validated_name})
        # save result
        appstruct['repo_group'] = appstruct_second['repo_group']

        # thirds to validate uniqueness
        third = RepoNameUniqueSchema().bind(**self.bindings)
        third.deserialize({'unique_repo_name': validated_name})

        return appstruct


class RepoSettingsSchema(RepoSchema):
    repo_group = colander.SchemaNode(
        colander.Integer(),
        validator=deferred_repo_group_validator,
        widget=deferred_repo_group_widget,
        missing='')

    repo_clone_uri_change = colander.SchemaNode(
        colander.String(),
        missing='NEW')

    repo_clone_uri = colander.SchemaNode(
        colander.String(),
        preparers=[preparers.strip_preparer],
        validator=deferred_sync_uri_validator,
        missing='')

    repo_push_uri_change = colander.SchemaNode(
        colander.String(),
        missing='NEW')

    repo_push_uri = colander.SchemaNode(
        colander.String(),
        preparers=[preparers.strip_preparer],
        validator=deferred_sync_uri_validator,
        missing='')

    def deserialize(self, cstruct):
        """
        Custom deserialize that allows to chain validation, and verify
        permissions, and as last step uniqueness
        """

        # first pass, to validate given data
        appstruct = super(RepoSchema, self).deserialize(cstruct)
        validated_name = appstruct['repo_name']
        # because of repoSchema adds repo-group as an ID, we inject it as
        # full name here because validators require it, it's unwrapped later
        # so it's safe to use and final name is going to be without group anyway

        group, separator = get_repo_group(appstruct['repo_group'])
        if group:
            validated_name = separator.join([group.group_name, validated_name])

        # second pass to validate permissions to repo_group
        if 'old_values' in self.bindings:
            # save current repo name for name change checks
            self.bindings['old_values']['submitted_repo_name'] = validated_name
        second = RepoGroupAccessSchema().bind(**self.bindings)
        appstruct_second = second.deserialize({'repo_group': validated_name})
        # save result
        appstruct['repo_group'] = appstruct_second['repo_group']

        # thirds to validate uniqueness
        third = RepoNameUniqueSchema().bind(**self.bindings)
        third.deserialize({'unique_repo_name': validated_name})

        return appstruct
