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

"""
this is forms validation classes
http://formencode.org/module-formencode.validators.html
for list off all availible validators

we can create our own validators

The table below outlines the options which can be used in a schema in addition to the validators themselves
pre_validators          []     These validators will be applied before the schema
chained_validators      []     These validators will be applied after the schema
allow_extra_fields      False     If True, then it is not an error when keys that aren't associated with a validator are present
filter_extra_fields     False     If True, then keys that aren't associated with a validator are removed
if_key_missing          NoDefault If this is given, then any keys that aren't available but are expected will be replaced with this value (and then validated). This does not override a present .if_missing attribute on validators. NoDefault is a special FormEncode class to mean that no default values has been specified and therefore missing keys shouldn't take a default value.
ignore_key_missing      False     If True, then missing keys will be missing in the result, if the validator doesn't have .if_missing on it already


<name> = formencode.validators.<name of validator>
<name> must equal form name
list=[1,2,3,4,5]
for SELECT use formencode.All(OneOf(list), Int())

"""

import deform
import logging
import formencode

from pkg_resources import resource_filename
from formencode import All, Pipe

from pyramid.threadlocal import get_current_request

from rhodecode import BACKENDS
from rhodecode.lib import helpers
from rhodecode.model import validators as v

log = logging.getLogger(__name__)


deform_templates = resource_filename('deform', 'templates')
rhodecode_templates = resource_filename('rhodecode', 'templates/forms')
search_path = (rhodecode_templates, deform_templates)


class RhodecodeFormZPTRendererFactory(deform.ZPTRendererFactory):
    """ Subclass of ZPTRendererFactory to add rhodecode context variables """
    def __call__(self, template_name, **kw):
        kw['h'] = helpers
        kw['request'] = get_current_request()
        return self.load(template_name)(**kw)


form_renderer = RhodecodeFormZPTRendererFactory(search_path)
deform.Form.set_default_renderer(form_renderer)


def LoginForm(localizer):
    _ = localizer

    class _LoginForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        username = v.UnicodeString(
            strip=True,
            min=1,
            not_empty=True,
            messages={
                'empty': _(u'Please enter a login'),
                'tooShort': _(u'Enter a value %(min)i characters long or more')
            }
        )

        password = v.UnicodeString(
            strip=False,
            min=3,
            max=72,
            not_empty=True,
            messages={
                'empty': _(u'Please enter a password'),
                'tooShort': _(u'Enter %(min)i characters or more')}
        )

        remember = v.StringBoolean(if_missing=False)

        chained_validators = [v.ValidAuth(localizer)]
    return _LoginForm


def UserForm(localizer, edit=False, available_languages=None, old_data=None):
    old_data = old_data or {}
    available_languages = available_languages or []
    _ = localizer

    class _UserForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        username = All(v.UnicodeString(strip=True, min=1, not_empty=True),
                       v.ValidUsername(localizer, edit, old_data))
        if edit:
            new_password = All(
                v.ValidPassword(localizer),
                v.UnicodeString(strip=False, min=6, max=72, not_empty=False)
            )
            password_confirmation = All(
                v.ValidPassword(localizer),
                v.UnicodeString(strip=False, min=6, max=72, not_empty=False),
            )
            admin = v.StringBoolean(if_missing=False)
        else:
            password = All(
                v.ValidPassword(localizer),
                v.UnicodeString(strip=False, min=6, max=72, not_empty=True)
            )
            password_confirmation = All(
                v.ValidPassword(localizer),
                v.UnicodeString(strip=False, min=6, max=72, not_empty=False)
            )

        password_change = v.StringBoolean(if_missing=False)
        create_repo_group = v.StringBoolean(if_missing=False)

        active = v.StringBoolean(if_missing=False)
        firstname = v.UnicodeString(strip=True, min=1, not_empty=False)
        lastname = v.UnicodeString(strip=True, min=1, not_empty=False)
        email = All(v.UniqSystemEmail(localizer, old_data), v.Email(not_empty=True))
        extern_name = v.UnicodeString(strip=True)
        extern_type = v.UnicodeString(strip=True)
        language = v.OneOf(available_languages, hideList=False,
                           testValueList=True, if_missing=None)
        chained_validators = [v.ValidPasswordsMatch(localizer)]
    return _UserForm


def UserGroupForm(localizer, edit=False, old_data=None, allow_disabled=False):
    old_data = old_data or {}
    _ = localizer

    class _UserGroupForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True

        users_group_name = All(
            v.UnicodeString(strip=True, min=1, not_empty=True),
            v.ValidUserGroup(localizer, edit, old_data)
        )
        user_group_description = v.UnicodeString(strip=True, min=1,
                                                 not_empty=False)

        users_group_active = v.StringBoolean(if_missing=False)

        if edit:
            # this is user group owner
            user = All(
                v.UnicodeString(not_empty=True),
                v.ValidRepoUser(localizer, allow_disabled))
    return _UserGroupForm


def RepoGroupForm(localizer, edit=False, old_data=None, available_groups=None,
                  can_create_in_root=False, allow_disabled=False):
    _ = localizer
    old_data = old_data or {}
    available_groups = available_groups or []

    class _RepoGroupForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False

        group_name = All(v.UnicodeString(strip=True, min=1, not_empty=True),
                         v.SlugifyName(localizer),)
        group_description = v.UnicodeString(strip=True, min=1,
                                            not_empty=False)
        group_copy_permissions = v.StringBoolean(if_missing=False)

        group_parent_id = v.OneOf(available_groups, hideList=False,
                                  testValueList=True, not_empty=True)
        enable_locking = v.StringBoolean(if_missing=False)
        chained_validators = [
            v.ValidRepoGroup(localizer, edit, old_data, can_create_in_root)]

        if edit:
            # this is repo group owner
            user = All(
                v.UnicodeString(not_empty=True),
                v.ValidRepoUser(localizer, allow_disabled))
    return _RepoGroupForm


def RegisterForm(localizer, edit=False, old_data=None):
    _ = localizer
    old_data = old_data or {}

    class _RegisterForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        username = All(
            v.ValidUsername(localizer, edit, old_data),
            v.UnicodeString(strip=True, min=1, not_empty=True)
        )
        password = All(
            v.ValidPassword(localizer),
            v.UnicodeString(strip=False, min=6, max=72, not_empty=True)
        )
        password_confirmation = All(
            v.ValidPassword(localizer),
            v.UnicodeString(strip=False, min=6, max=72, not_empty=True)
        )
        active = v.StringBoolean(if_missing=False)
        firstname = v.UnicodeString(strip=True, min=1, not_empty=False)
        lastname = v.UnicodeString(strip=True, min=1, not_empty=False)
        email = All(v.UniqSystemEmail(localizer, old_data), v.Email(not_empty=True))

        chained_validators = [v.ValidPasswordsMatch(localizer)]
    return _RegisterForm


def PasswordResetForm(localizer):
    _ = localizer

    class _PasswordResetForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        email = All(v.ValidSystemEmail(localizer), v.Email(not_empty=True))
    return _PasswordResetForm


def RepoForm(localizer, edit=False, old_data=None, repo_groups=None,
             landing_revs=None, allow_disabled=False):
    _ = localizer
    old_data = old_data or {}
    repo_groups = repo_groups or []
    landing_revs = landing_revs or []
    supported_backends = BACKENDS.keys()

    class _RepoForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(v.UnicodeString(strip=True, min=1, not_empty=True),
                        v.SlugifyName(localizer), v.CannotHaveGitSuffix(localizer))
        repo_group = All(v.CanWriteGroup(localizer, old_data),
                         v.OneOf(repo_groups, hideList=True))
        repo_type = v.OneOf(supported_backends, required=False,
                            if_missing=old_data.get('repo_type'))
        repo_description = v.UnicodeString(strip=True, min=1, not_empty=False)
        repo_private = v.StringBoolean(if_missing=False)
        repo_landing_rev = v.OneOf(landing_revs, hideList=True)
        repo_copy_permissions = v.StringBoolean(if_missing=False)
        clone_uri = All(v.UnicodeString(strip=True, min=1, not_empty=False))

        repo_enable_statistics = v.StringBoolean(if_missing=False)
        repo_enable_downloads = v.StringBoolean(if_missing=False)
        repo_enable_locking = v.StringBoolean(if_missing=False)

        if edit:
            # this is repo owner
            user = All(
                v.UnicodeString(not_empty=True),
                v.ValidRepoUser(localizer, allow_disabled))
            clone_uri_change = v.UnicodeString(
                not_empty=False, if_missing=v.Missing)

        chained_validators = [v.ValidCloneUri(localizer),
                              v.ValidRepoName(localizer, edit, old_data)]
    return _RepoForm


def RepoPermsForm(localizer):
    _ = localizer

    class _RepoPermsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        chained_validators = [v.ValidPerms(localizer, type_='repo')]
    return _RepoPermsForm


def RepoGroupPermsForm(localizer, valid_recursive_choices):
    _ = localizer

    class _RepoGroupPermsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        recursive = v.OneOf(valid_recursive_choices)
        chained_validators = [v.ValidPerms(localizer, type_='repo_group')]
    return _RepoGroupPermsForm


def UserGroupPermsForm(localizer):
    _ = localizer

    class _UserPermsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        chained_validators = [v.ValidPerms(localizer, type_='user_group')]
    return _UserPermsForm


def RepoFieldForm(localizer):
    _ = localizer

    class _RepoFieldForm(formencode.Schema):
        filter_extra_fields = True
        allow_extra_fields = True

        new_field_key = All(v.FieldKey(localizer),
                            v.UnicodeString(strip=True, min=3, not_empty=True))
        new_field_value = v.UnicodeString(not_empty=False, if_missing=u'')
        new_field_type = v.OneOf(['str', 'unicode', 'list', 'tuple'],
                                 if_missing='str')
        new_field_label = v.UnicodeString(not_empty=False)
        new_field_desc = v.UnicodeString(not_empty=False)
    return _RepoFieldForm


def RepoForkForm(localizer, edit=False, old_data=None,
                 supported_backends=BACKENDS.keys(), repo_groups=None,
                 landing_revs=None):
    _ = localizer
    old_data = old_data or {}
    repo_groups = repo_groups or []
    landing_revs = landing_revs or []

    class _RepoForkForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(v.UnicodeString(strip=True, min=1, not_empty=True),
                        v.SlugifyName(localizer))
        repo_group = All(v.CanWriteGroup(localizer, ),
                         v.OneOf(repo_groups, hideList=True))
        repo_type = All(v.ValidForkType(localizer, old_data), v.OneOf(supported_backends))
        description = v.UnicodeString(strip=True, min=1, not_empty=True)
        private = v.StringBoolean(if_missing=False)
        copy_permissions = v.StringBoolean(if_missing=False)
        fork_parent_id = v.UnicodeString()
        chained_validators = [v.ValidForkName(localizer, edit, old_data)]
        landing_rev = v.OneOf(landing_revs, hideList=True)
    return _RepoForkForm


def ApplicationSettingsForm(localizer):
    _ = localizer

    class _ApplicationSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        rhodecode_title = v.UnicodeString(strip=True, max=40, not_empty=False)
        rhodecode_realm = v.UnicodeString(strip=True, min=1, not_empty=True)
        rhodecode_pre_code = v.UnicodeString(strip=True, min=1, not_empty=False)
        rhodecode_post_code = v.UnicodeString(strip=True, min=1, not_empty=False)
        rhodecode_captcha_public_key = v.UnicodeString(strip=True, min=1, not_empty=False)
        rhodecode_captcha_private_key = v.UnicodeString(strip=True, min=1, not_empty=False)
        rhodecode_create_personal_repo_group = v.StringBoolean(if_missing=False)
        rhodecode_personal_repo_group_pattern = v.UnicodeString(strip=True, min=1, not_empty=False)
    return _ApplicationSettingsForm


def ApplicationVisualisationForm(localizer):
    from rhodecode.model.db import Repository
    _ = localizer

    class _ApplicationVisualisationForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        rhodecode_show_public_icon = v.StringBoolean(if_missing=False)
        rhodecode_show_private_icon = v.StringBoolean(if_missing=False)
        rhodecode_stylify_metatags = v.StringBoolean(if_missing=False)

        rhodecode_repository_fields = v.StringBoolean(if_missing=False)
        rhodecode_lightweight_journal = v.StringBoolean(if_missing=False)
        rhodecode_dashboard_items = v.Int(min=5, not_empty=True)
        rhodecode_admin_grid_items = v.Int(min=5, not_empty=True)
        rhodecode_show_version = v.StringBoolean(if_missing=False)
        rhodecode_use_gravatar = v.StringBoolean(if_missing=False)
        rhodecode_markup_renderer = v.OneOf(['markdown', 'rst'])
        rhodecode_gravatar_url = v.UnicodeString(min=3)
        rhodecode_clone_uri_tmpl = v.UnicodeString(not_empty=False, if_empty=Repository.DEFAULT_CLONE_URI)
        rhodecode_clone_uri_ssh_tmpl = v.UnicodeString(not_empty=False, if_empty=Repository.DEFAULT_CLONE_URI_SSH)
        rhodecode_support_url = v.UnicodeString()
        rhodecode_show_revision_number = v.StringBoolean(if_missing=False)
        rhodecode_show_sha_length = v.Int(min=4, not_empty=True)
    return _ApplicationVisualisationForm


class _BaseVcsSettingsForm(formencode.Schema):

    allow_extra_fields = True
    filter_extra_fields = False
    hooks_changegroup_repo_size = v.StringBoolean(if_missing=False)
    hooks_changegroup_push_logger = v.StringBoolean(if_missing=False)
    hooks_outgoing_pull_logger = v.StringBoolean(if_missing=False)

    # PR/Code-review
    rhodecode_pr_merge_enabled = v.StringBoolean(if_missing=False)
    rhodecode_use_outdated_comments = v.StringBoolean(if_missing=False)

    # hg
    extensions_largefiles = v.StringBoolean(if_missing=False)
    extensions_evolve = v.StringBoolean(if_missing=False)
    phases_publish = v.StringBoolean(if_missing=False)

    rhodecode_hg_use_rebase_for_merging = v.StringBoolean(if_missing=False)
    rhodecode_hg_close_branch_before_merging = v.StringBoolean(if_missing=False)

    # git
    vcs_git_lfs_enabled = v.StringBoolean(if_missing=False)
    rhodecode_git_use_rebase_for_merging = v.StringBoolean(if_missing=False)
    rhodecode_git_close_branch_before_merging = v.StringBoolean(if_missing=False)

    # svn
    vcs_svn_proxy_http_requests_enabled = v.StringBoolean(if_missing=False)
    vcs_svn_proxy_http_server_url = v.UnicodeString(strip=True, if_missing=None)

    # cache
    rhodecode_diff_cache = v.StringBoolean(if_missing=False)


def ApplicationUiSettingsForm(localizer):
    _ = localizer

    class _ApplicationUiSettingsForm(_BaseVcsSettingsForm):
        web_push_ssl = v.StringBoolean(if_missing=False)
        paths_root_path = All(
            v.ValidPath(localizer),
            v.UnicodeString(strip=True, min=1, not_empty=True)
        )
        largefiles_usercache = All(
            v.ValidPath(localizer),
            v.UnicodeString(strip=True, min=2, not_empty=True))
        vcs_git_lfs_store_location = All(
            v.ValidPath(localizer),
            v.UnicodeString(strip=True, min=2, not_empty=True))
        extensions_hgsubversion = v.StringBoolean(if_missing=False)
        extensions_hggit = v.StringBoolean(if_missing=False)
        new_svn_branch = v.ValidSvnPattern(localizer, section='vcs_svn_branch')
        new_svn_tag = v.ValidSvnPattern(localizer, section='vcs_svn_tag')
    return _ApplicationUiSettingsForm


def RepoVcsSettingsForm(localizer, repo_name):
    _ = localizer

    class _RepoVcsSettingsForm(_BaseVcsSettingsForm):
        inherit_global_settings = v.StringBoolean(if_missing=False)
        new_svn_branch = v.ValidSvnPattern(localizer,
            section='vcs_svn_branch', repo_name=repo_name)
        new_svn_tag = v.ValidSvnPattern(localizer,
            section='vcs_svn_tag', repo_name=repo_name)
    return _RepoVcsSettingsForm


def LabsSettingsForm(localizer):
    _ = localizer

    class _LabSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
    return _LabSettingsForm


def ApplicationPermissionsForm(
        localizer, register_choices, password_reset_choices,
        extern_activate_choices):
    _ = localizer

    class _DefaultPermissionsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True

        anonymous = v.StringBoolean(if_missing=False)
        default_register = v.OneOf(register_choices)
        default_register_message = v.UnicodeString()
        default_password_reset = v.OneOf(password_reset_choices)
        default_extern_activate = v.OneOf(extern_activate_choices)
    return _DefaultPermissionsForm


def ObjectPermissionsForm(localizer, repo_perms_choices, group_perms_choices,
                          user_group_perms_choices):
    _ = localizer

    class _ObjectPermissionsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        overwrite_default_repo = v.StringBoolean(if_missing=False)
        overwrite_default_group = v.StringBoolean(if_missing=False)
        overwrite_default_user_group = v.StringBoolean(if_missing=False)

        default_repo_perm = v.OneOf(repo_perms_choices)
        default_group_perm = v.OneOf(group_perms_choices)
        default_user_group_perm = v.OneOf(user_group_perms_choices)

    return _ObjectPermissionsForm


def BranchPermissionsForm(localizer, branch_perms_choices):
    _ = localizer

    class _BranchPermissionsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        overwrite_default_branch = v.StringBoolean(if_missing=False)
        default_branch_perm = v.OneOf(branch_perms_choices)

    return _BranchPermissionsForm


def UserPermissionsForm(localizer, create_choices, create_on_write_choices,
                        repo_group_create_choices, user_group_create_choices,
                        fork_choices, inherit_default_permissions_choices):
    _ = localizer

    class _DefaultPermissionsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True

        anonymous = v.StringBoolean(if_missing=False)

        default_repo_create = v.OneOf(create_choices)
        default_repo_create_on_write = v.OneOf(create_on_write_choices)
        default_user_group_create = v.OneOf(user_group_create_choices)
        default_repo_group_create = v.OneOf(repo_group_create_choices)
        default_fork_create = v.OneOf(fork_choices)
        default_inherit_default_permissions = v.OneOf(inherit_default_permissions_choices)
    return _DefaultPermissionsForm


def UserIndividualPermissionsForm(localizer):
    _ = localizer

    class _DefaultPermissionsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True

        inherit_default_permissions = v.StringBoolean(if_missing=False)
    return _DefaultPermissionsForm


def DefaultsForm(localizer, edit=False, old_data=None, supported_backends=BACKENDS.keys()):
    _ = localizer
    old_data = old_data or {}

    class _DefaultsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        default_repo_type = v.OneOf(supported_backends)
        default_repo_private = v.StringBoolean(if_missing=False)
        default_repo_enable_statistics = v.StringBoolean(if_missing=False)
        default_repo_enable_downloads = v.StringBoolean(if_missing=False)
        default_repo_enable_locking = v.StringBoolean(if_missing=False)
    return _DefaultsForm


def AuthSettingsForm(localizer):
    _ = localizer

    class _AuthSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        auth_plugins = All(v.ValidAuthPlugins(localizer),
                           v.UniqueListFromString(localizer)(not_empty=True))
    return _AuthSettingsForm


def UserExtraEmailForm(localizer):
    _ = localizer

    class _UserExtraEmailForm(formencode.Schema):
        email = All(v.UniqSystemEmail(localizer), v.Email(not_empty=True))
    return _UserExtraEmailForm


def UserExtraIpForm(localizer):
    _ = localizer

    class _UserExtraIpForm(formencode.Schema):
        ip = v.ValidIp(localizer)(not_empty=True)
    return _UserExtraIpForm


def PullRequestForm(localizer, repo_id):
    _ = localizer

    class ReviewerForm(formencode.Schema):
        user_id = v.Int(not_empty=True)
        reasons = All()
        rules = All(v.UniqueList(localizer, convert=int)())
        mandatory = v.StringBoolean()

    class _PullRequestForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True

        common_ancestor = v.UnicodeString(strip=True, required=True)
        source_repo = v.UnicodeString(strip=True, required=True)
        source_ref = v.UnicodeString(strip=True, required=True)
        target_repo = v.UnicodeString(strip=True, required=True)
        target_ref = v.UnicodeString(strip=True, required=True)
        revisions = All(#v.NotReviewedRevisions(localizer, repo_id)(),
                        v.UniqueList(localizer)(not_empty=True))
        review_members = formencode.ForEach(ReviewerForm())
        pullrequest_title = v.UnicodeString(strip=True, required=True, min=3, max=255)
        pullrequest_desc = v.UnicodeString(strip=True, required=False)
        description_renderer = v.UnicodeString(strip=True, required=False)

    return _PullRequestForm


def IssueTrackerPatternsForm(localizer):
    _ = localizer

    class _IssueTrackerPatternsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        chained_validators = [v.ValidPattern(localizer)]
    return _IssueTrackerPatternsForm
