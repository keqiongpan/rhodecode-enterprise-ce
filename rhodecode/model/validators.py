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

"""
Set of generic validators
"""


import os
import re
import logging
import collections

import formencode
import ipaddress
from formencode.validators import (
    UnicodeString, OneOf, Int, Number, Regex, Email, Bool, StringBoolean, Set,
    NotEmpty, IPAddress, CIDR, String, FancyValidator
)

from sqlalchemy.sql.expression import true
from sqlalchemy.util import OrderedSet
from pyramid import compat

from rhodecode.authentication import (
    legacy_plugin_prefix, _import_legacy_plugin)
from rhodecode.authentication.base import loadplugin
from rhodecode.apps._base import ADMIN_PREFIX
from rhodecode.lib.auth import HasRepoGroupPermissionAny, HasPermissionAny
from rhodecode.lib.utils import repo_name_slug, make_db_config
from rhodecode.lib.utils2 import safe_int, str2bool, aslist, md5, safe_unicode
from rhodecode.lib.vcs.backends.git.repository import GitRepository
from rhodecode.lib.vcs.backends.hg.repository import MercurialRepository
from rhodecode.lib.vcs.backends.svn.repository import SubversionRepository
from rhodecode.model.db import (
    RepoGroup, Repository, UserGroup, User, ChangesetStatus, Gist)
from rhodecode.model.settings import VcsSettingsModel

# silence warnings and pylint
UnicodeString, OneOf, Int, Number, Regex, Email, Bool, StringBoolean, Set, \
    NotEmpty, IPAddress, CIDR, String, FancyValidator

log = logging.getLogger(__name__)


class _Missing(object):
    pass


Missing = _Missing()


def M(self, key, state, **kwargs):
    """
    returns string from self.message based on given key,
    passed kw params are used to substitute %(named)s params inside
    translated strings

    :param msg:
    :param state:
    """

    #state._ = staticmethod(_)
    # inject validator into state object
    return self.message(key, state, **kwargs)


def UniqueList(localizer, convert=None):
    _ = localizer

    class _validator(formencode.FancyValidator):
        """
        Unique List !
        """
        messages = {
            'empty': _(u'Value cannot be an empty list'),
            'missing_value': _(u'Value cannot be an empty list'),
        }

        def _to_python(self, value, state):
            ret_val = []

            def make_unique(value):
                seen = []
                return [c for c in value if not (c in seen or seen.append(c))]

            if isinstance(value, list):
                ret_val = make_unique(value)
            elif isinstance(value, set):
                ret_val = make_unique(list(value))
            elif isinstance(value, tuple):
                ret_val = make_unique(list(value))
            elif value is None:
                ret_val = []
            else:
                ret_val = [value]

            if convert:
                ret_val = map(convert, ret_val)
            return ret_val

        def empty_value(self, value):
            return []
    return _validator


def UniqueListFromString(localizer):
    _ = localizer

    class _validator(UniqueList(localizer)):
        def _to_python(self, value, state):
            if isinstance(value, compat.string_types):
                value = aslist(value, ',')
            return super(_validator, self)._to_python(value, state)
    return _validator


def ValidSvnPattern(localizer, section, repo_name=None):
    _ = localizer

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'pattern_exists': _(u'Pattern already exists'),
        }

        def validate_python(self, value, state):
            if not value:
                return
            model = VcsSettingsModel(repo=repo_name)
            ui_settings = model.get_svn_patterns(section=section)
            for entry in ui_settings:
                if value == entry.value:
                    msg = M(self, 'pattern_exists', state)
                    raise formencode.Invalid(msg, value, state)
    return _validator


def ValidUsername(localizer, edit=False, old_data=None):
    _ = localizer
    old_data = old_data or {}

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'username_exists': _(u'Username "%(username)s" already exists'),
            'system_invalid_username':
                _(u'Username "%(username)s" is forbidden'),
            'invalid_username':
                _(u'Username may only contain alphanumeric characters '
                    u'underscores, periods or dashes and must begin with '
                    u'alphanumeric character or underscore')
        }

        def validate_python(self, value, state):
            if value in ['default', 'new_user']:
                msg = M(self, 'system_invalid_username', state, username=value)
                raise formencode.Invalid(msg, value, state)
            # check if user is unique
            old_un = None
            if edit:
                old_un = User.get(old_data.get('user_id')).username

            if old_un != value or not edit:
                if User.get_by_username(value, case_insensitive=True):
                    msg = M(self, 'username_exists', state, username=value)
                    raise formencode.Invalid(msg, value, state)

            if (re.match(r'^[\w]{1}[\w\-\.]{0,254}$', value)
                    is None):
                msg = M(self, 'invalid_username', state)
                raise formencode.Invalid(msg, value, state)
    return _validator


def ValidRepoUser(localizer, allow_disabled=False):
    _ = localizer

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'invalid_username': _(u'Username %(username)s is not valid'),
            'disabled_username': _(u'Username %(username)s is disabled')
        }

        def validate_python(self, value, state):
            try:
                user = User.query().filter(User.username == value).one()
            except Exception:
                msg = M(self, 'invalid_username', state, username=value)
                raise formencode.Invalid(
                    msg, value, state, error_dict={'username': msg}
                )
            if user and (not allow_disabled and not user.active):
                msg = M(self, 'disabled_username', state, username=value)
                raise formencode.Invalid(
                    msg, value, state, error_dict={'username': msg}
                )
    return _validator


def ValidUserGroup(localizer, edit=False, old_data=None):
    _ = localizer
    old_data = old_data or {}

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'invalid_group': _(u'Invalid user group name'),
            'group_exist': _(u'User group `%(usergroup)s` already exists'),
            'invalid_usergroup_name':
                _(u'user group name may only contain alphanumeric '
                  u'characters underscores, periods or dashes and must begin '
                  u'with alphanumeric character')
        }

        def validate_python(self, value, state):
            if value in ['default']:
                msg = M(self, 'invalid_group', state)
                raise formencode.Invalid(
                    msg, value, state, error_dict={'users_group_name': msg}
                )
            # check if group is unique
            old_ugname = None
            if edit:
                old_id = old_data.get('users_group_id')
                old_ugname = UserGroup.get(old_id).users_group_name

            if old_ugname != value or not edit:
                is_existing_group = UserGroup.get_by_group_name(
                    value, case_insensitive=True)
                if is_existing_group:
                    msg = M(self, 'group_exist', state, usergroup=value)
                    raise formencode.Invalid(
                        msg, value, state, error_dict={'users_group_name': msg}
                    )

            if re.match(r'^[a-zA-Z0-9]{1}[a-zA-Z0-9\-\_\.]+$', value) is None:
                msg = M(self, 'invalid_usergroup_name', state)
                raise formencode.Invalid(
                    msg, value, state, error_dict={'users_group_name': msg}
                )
    return _validator


def ValidRepoGroup(localizer, edit=False, old_data=None, can_create_in_root=False):
    _ = localizer
    old_data = old_data or {}

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'group_parent_id': _(u'Cannot assign this group as parent'),
            'group_exists': _(u'Group "%(group_name)s" already exists'),
            'repo_exists': _(u'Repository with name "%(group_name)s" '
                             u'already exists'),
            'permission_denied': _(u"no permission to store repository group"
                                   u"in this location"),
            'permission_denied_root': _(
                u"no permission to store repository group "
                u"in root location")
        }

        def _to_python(self, value, state):
            group_name = repo_name_slug(value.get('group_name', ''))
            group_parent_id = safe_int(value.get('group_parent_id'))
            gr = RepoGroup.get(group_parent_id)
            if gr:
                parent_group_path = gr.full_path
                # value needs to be aware of group name in order to check
                # db key This is an actual just the name to store in the
                # database
                group_name_full = (
                    parent_group_path + RepoGroup.url_sep() + group_name)
            else:
                group_name_full = group_name

            value['group_name'] = group_name
            value['group_name_full'] = group_name_full
            value['group_parent_id'] = group_parent_id
            return value

        def validate_python(self, value, state):

            old_group_name = None
            group_name = value.get('group_name')
            group_name_full = value.get('group_name_full')
            group_parent_id = safe_int(value.get('group_parent_id'))
            if group_parent_id == -1:
                group_parent_id = None

            group_obj = RepoGroup.get(old_data.get('group_id'))
            parent_group_changed = False
            if edit:
                old_group_name = group_obj.group_name
                old_group_parent_id = group_obj.group_parent_id

                if group_parent_id != old_group_parent_id:
                    parent_group_changed = True

                # TODO: mikhail: the following if statement is not reached
                # since group_parent_id's OneOf validation fails before.
                # Can be removed.

                # check against setting a parent of self
                parent_of_self = (
                    old_data['group_id'] == group_parent_id
                    if group_parent_id else False
                )
                if parent_of_self:
                    msg = M(self, 'group_parent_id', state)
                    raise formencode.Invalid(
                        msg, value, state, error_dict={'group_parent_id': msg}
                    )

            # group we're moving current group inside
            child_group = None
            if group_parent_id:
                child_group = RepoGroup.query().filter(
                    RepoGroup.group_id == group_parent_id).scalar()

            # do a special check that we cannot move a group to one of
            # it's children
            if edit and child_group:
                parents = [x.group_id for x in child_group.parents]
                move_to_children = old_data['group_id'] in parents
                if move_to_children:
                    msg = M(self, 'group_parent_id', state)
                    raise formencode.Invalid(
                        msg, value, state, error_dict={'group_parent_id': msg})

            # Check if we have permission to store in the parent.
            # Only check if the parent group changed.
            if parent_group_changed:
                if child_group is None:
                    if not can_create_in_root:
                        msg = M(self, 'permission_denied_root', state)
                        raise formencode.Invalid(
                            msg, value, state,
                            error_dict={'group_parent_id': msg})
                else:
                    valid = HasRepoGroupPermissionAny('group.admin')
                    forbidden = not valid(
                        child_group.group_name, 'can create group validator')
                    if forbidden:
                        msg = M(self, 'permission_denied', state)
                        raise formencode.Invalid(
                            msg, value, state,
                            error_dict={'group_parent_id': msg})

            # if we change the name or it's new group, check for existing names
            # or repositories with the same name
            if old_group_name != group_name_full or not edit:
                # check group
                gr = RepoGroup.get_by_group_name(group_name_full)
                if gr:
                    msg = M(self, 'group_exists', state, group_name=group_name)
                    raise formencode.Invalid(
                        msg, value, state, error_dict={'group_name': msg})

                # check for same repo
                repo = Repository.get_by_repo_name(group_name_full)
                if repo:
                    msg = M(self, 'repo_exists', state, group_name=group_name)
                    raise formencode.Invalid(
                        msg, value, state, error_dict={'group_name': msg})
    return _validator


def ValidPassword(localizer):
    _ = localizer

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'invalid_password':
                _(u'Invalid characters (non-ascii) in password')
        }

        def validate_python(self, value, state):
            try:
                (value or '').decode('ascii')
            except UnicodeError:
                msg = M(self, 'invalid_password', state)
                raise formencode.Invalid(msg, value, state,)
    return _validator


def ValidPasswordsMatch(
        localizer, passwd='new_password',
        passwd_confirmation='password_confirmation'):
    _ = localizer

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'password_mismatch': _(u'Passwords do not match'),
        }

        def validate_python(self, value, state):

            pass_val = value.get('password') or value.get(passwd)
            if pass_val != value[passwd_confirmation]:
                msg = M(self, 'password_mismatch', state)
                raise formencode.Invalid(
                    msg, value, state,
                    error_dict={passwd: msg, passwd_confirmation: msg}
                )
    return _validator


def ValidAuth(localizer):
    _ = localizer

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'invalid_password': _(u'invalid password'),
            'invalid_username': _(u'invalid user name'),
            'disabled_account': _(u'Your account is disabled')
        }

        def validate_python(self, value, state):
            from rhodecode.authentication.base import authenticate, HTTP_TYPE

            password = value['password']
            username = value['username']

            if not authenticate(username, password, '', HTTP_TYPE,
                                skip_missing=True):
                user = User.get_by_username(username)
                if user and not user.active:
                    log.warning('user %s is disabled', username)
                    msg = M(self, 'disabled_account', state)
                    raise formencode.Invalid(
                        msg, value, state, error_dict={'username': msg}
                    )
                else:
                    log.warning('user `%s` failed to authenticate', username)
                    msg = M(self, 'invalid_username', state)
                    msg2 = M(self, 'invalid_password', state)
                    raise formencode.Invalid(
                        msg, value, state,
                        error_dict={'username': msg, 'password': msg2}
                    )
    return _validator


def ValidRepoName(localizer, edit=False, old_data=None):
    old_data = old_data or {}
    _ = localizer

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'invalid_repo_name':
                _(u'Repository name %(repo)s is disallowed'),
            # top level
            'repository_exists': _(u'Repository with name %(repo)s '
                                   u'already exists'),
            'group_exists': _(u'Repository group with name "%(repo)s" '
                              u'already exists'),
            # inside a group
            'repository_in_group_exists': _(u'Repository with name %(repo)s '
                                            u'exists in group "%(group)s"'),
            'group_in_group_exists': _(
                u'Repository group with name "%(repo)s" '
                u'exists in group "%(group)s"'),
        }

        def _to_python(self, value, state):
            repo_name = repo_name_slug(value.get('repo_name', ''))
            repo_group = value.get('repo_group')
            if repo_group:
                gr = RepoGroup.get(repo_group)
                group_path = gr.full_path
                group_name = gr.group_name
                # value needs to be aware of group name in order to check
                # db key This is an actual just the name to store in the
                # database
                repo_name_full = group_path + RepoGroup.url_sep() + repo_name
            else:
                group_name = group_path = ''
                repo_name_full = repo_name

            value['repo_name'] = repo_name
            value['repo_name_full'] = repo_name_full
            value['group_path'] = group_path
            value['group_name'] = group_name
            return value

        def validate_python(self, value, state):

            repo_name = value.get('repo_name')
            repo_name_full = value.get('repo_name_full')
            group_path = value.get('group_path')
            group_name = value.get('group_name')

            if repo_name in [ADMIN_PREFIX, '']:
                msg = M(self, 'invalid_repo_name', state, repo=repo_name)
                raise formencode.Invalid(
                    msg, value, state, error_dict={'repo_name': msg})

            rename = old_data.get('repo_name') != repo_name_full
            create = not edit
            if rename or create:

                if group_path:
                    if Repository.get_by_repo_name(repo_name_full):
                        msg = M(self, 'repository_in_group_exists', state,
                                repo=repo_name, group=group_name)
                        raise formencode.Invalid(
                            msg, value, state, error_dict={'repo_name': msg})
                    if RepoGroup.get_by_group_name(repo_name_full):
                        msg = M(self, 'group_in_group_exists', state,
                                repo=repo_name, group=group_name)
                        raise formencode.Invalid(
                            msg, value, state, error_dict={'repo_name': msg})
                else:
                    if RepoGroup.get_by_group_name(repo_name_full):
                        msg = M(self, 'group_exists', state, repo=repo_name)
                        raise formencode.Invalid(
                            msg, value, state, error_dict={'repo_name': msg})

                    if Repository.get_by_repo_name(repo_name_full):
                        msg = M(
                            self, 'repository_exists', state, repo=repo_name)
                        raise formencode.Invalid(
                            msg, value, state, error_dict={'repo_name': msg})
            return value
    return _validator


def ValidForkName(localizer, *args, **kwargs):
    _ = localizer

    return ValidRepoName(localizer, *args, **kwargs)


def SlugifyName(localizer):
    _ = localizer
    
    class _validator(formencode.validators.FancyValidator):

        def _to_python(self, value, state):
            return repo_name_slug(value)

        def validate_python(self, value, state):
            pass
    return _validator


def CannotHaveGitSuffix(localizer):
    _ = localizer
    
    class _validator(formencode.validators.FancyValidator):
        messages = {
            'has_git_suffix':
                _(u'Repository name cannot end with .git'),
        }

        def _to_python(self, value, state):
            return value

        def validate_python(self, value, state):
            if value and value.endswith('.git'):
                msg = M(
                    self, 'has_git_suffix', state)
                raise formencode.Invalid(
                    msg, value, state, error_dict={'repo_name': msg})
    return _validator


def ValidCloneUri(localizer):
    _ = localizer
    
    class InvalidCloneUrl(Exception):
        allowed_prefixes = ()

    def url_handler(repo_type, url):
        config = make_db_config(clear_session=False)
        if repo_type == 'hg':
            allowed_prefixes = ('http', 'svn+http', 'git+http')

            if 'http' in url[:4]:
                # initially check if it's at least the proper URL
                # or does it pass basic auth
                MercurialRepository.check_url(url, config)
            elif 'svn+http' in url[:8]:  # svn->hg import
                SubversionRepository.check_url(url, config)
            elif 'git+http' in url[:8]:  # git->hg import
                raise NotImplementedError()
            else:
                exc = InvalidCloneUrl('Clone from URI %s not allowed. '
                                      'Allowed url must start with one of %s'
                                      % (url, ','.join(allowed_prefixes)))
                exc.allowed_prefixes = allowed_prefixes
                raise exc

        elif repo_type == 'git':
            allowed_prefixes = ('http', 'svn+http', 'hg+http')
            if 'http' in url[:4]:
                # initially check if it's at least the proper URL
                # or does it pass basic auth
                GitRepository.check_url(url, config)
            elif 'svn+http' in url[:8]:  # svn->git import
                raise NotImplementedError()
            elif 'hg+http' in url[:8]:  # hg->git import
                raise NotImplementedError()
            else:
                exc = InvalidCloneUrl('Clone from URI %s not allowed. '
                                      'Allowed url must start with one of %s'
                                      % (url, ','.join(allowed_prefixes)))
                exc.allowed_prefixes = allowed_prefixes
                raise exc

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'clone_uri': _(u'invalid clone url for %(rtype)s repository'),
            'invalid_clone_uri': _(
                u'Invalid clone url, provide a valid clone '
                u'url starting with one of %(allowed_prefixes)s')
        }

        def validate_python(self, value, state):
            repo_type = value.get('repo_type')
            url = value.get('clone_uri')

            if url:
                try:
                    url_handler(repo_type, url)
                except InvalidCloneUrl as e:
                    log.warning(e)
                    msg = M(self, 'invalid_clone_uri', state, rtype=repo_type,
                            allowed_prefixes=','.join(e.allowed_prefixes))
                    raise formencode.Invalid(msg, value, state,
                                             error_dict={'clone_uri': msg})
                except Exception:
                    log.exception('Url validation failed')
                    msg = M(self, 'clone_uri', state, rtype=repo_type)
                    raise formencode.Invalid(msg, value, state,
                                             error_dict={'clone_uri': msg})
    return _validator


def ValidForkType(localizer, old_data=None):
    _ = localizer
    old_data = old_data or {}

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'invalid_fork_type': _(u'Fork have to be the same type as parent')
        }

        def validate_python(self, value, state):
            if old_data['repo_type'] != value:
                msg = M(self, 'invalid_fork_type', state)
                raise formencode.Invalid(
                    msg, value, state, error_dict={'repo_type': msg}
                )
    return _validator


def CanWriteGroup(localizer, old_data=None):
    _ = localizer

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'permission_denied': _(
                u"You do not have the permission "
                u"to create repositories in this group."),
            'permission_denied_root': _(
                u"You do not have the permission to store repositories in "
                u"the root location.")
        }

        def _to_python(self, value, state):
            # root location
            if value in [-1, "-1"]:
                return None
            return value

        def validate_python(self, value, state):
            gr = RepoGroup.get(value)
            gr_name = gr.group_name if gr else None  # None means ROOT location
            # create repositories with write permission on group is set to true
            create_on_write = HasPermissionAny(
                'hg.create.write_on_repogroup.true')()
            group_admin = HasRepoGroupPermissionAny('group.admin')(
                gr_name, 'can write into group validator')
            group_write = HasRepoGroupPermissionAny('group.write')(
                gr_name, 'can write into group validator')
            forbidden = not (group_admin or (group_write and create_on_write))
            can_create_repos = HasPermissionAny(
                'hg.admin', 'hg.create.repository')
            gid = (old_data['repo_group'].get('group_id')
                   if (old_data and 'repo_group' in old_data) else None)
            value_changed = gid != safe_int(value)
            new = not old_data
            # do check if we changed the value, there's a case that someone got
            # revoked write permissions to a repository, he still created, we
            # don't need to check permission if he didn't change the value of
            # groups in form box
            if value_changed or new:
                # parent group need to be existing
                if gr and forbidden:
                    msg = M(self, 'permission_denied', state)
                    raise formencode.Invalid(
                        msg, value, state, error_dict={'repo_type': msg}
                    )
                # check if we can write to root location !
                elif gr is None and not can_create_repos():
                    msg = M(self, 'permission_denied_root', state)
                    raise formencode.Invalid(
                        msg, value, state, error_dict={'repo_type': msg}
                    )
    return _validator


def ValidPerms(localizer, type_='repo'):
    _ = localizer
    if type_ == 'repo_group':
        EMPTY_PERM = 'group.none'
    elif type_ == 'repo':
        EMPTY_PERM = 'repository.none'
    elif type_ == 'user_group':
        EMPTY_PERM = 'usergroup.none'

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'perm_new_member_name':
                _(u'This username or user group name is not valid')
        }

        def _to_python(self, value, state):
            perm_updates = OrderedSet()
            perm_additions = OrderedSet()
            perm_deletions = OrderedSet()
            # build a list of permission to update/delete and new permission

            # Read the perm_new_member/perm_del_member attributes and group
            # them by they IDs
            new_perms_group = collections.defaultdict(dict)
            del_perms_group = collections.defaultdict(dict)
            for k, v in value.copy().iteritems():
                if k.startswith('perm_del_member'):
                    # delete from org storage so we don't process that later
                    del value[k]
                    # part is `id`, `type`
                    _type, part = k.split('perm_del_member_')
                    args = part.split('_')
                    if len(args) == 2:
                        _key, pos = args
                        del_perms_group[pos][_key] = v
                if k.startswith('perm_new_member'):
                    # delete from org storage so we don't process that later
                    del value[k]
                    # part is `id`, `type`, `perm`
                    _type, part = k.split('perm_new_member_')
                    args = part.split('_')
                    if len(args) == 2:
                        _key, pos = args
                        new_perms_group[pos][_key] = v

            # store the deletes
            for k in sorted(del_perms_group.keys()):
                perm_dict = del_perms_group[k]
                del_member = perm_dict.get('id')
                del_type = perm_dict.get('type')
                if del_member and del_type:
                    perm_deletions.add(
                        (del_member, None, del_type))

            # store additions in order of how they were added in web form
            for k in sorted(new_perms_group.keys()):
                perm_dict = new_perms_group[k]
                new_member = perm_dict.get('id')
                new_type = perm_dict.get('type')
                new_perm = perm_dict.get('perm')
                if new_member and new_perm and new_type:
                    perm_additions.add(
                        (new_member, new_perm, new_type))

            # get updates of permissions
            # (read the existing radio button states)
            default_user_id = User.get_default_user_id()

            for k, update_value in value.iteritems():
                if k.startswith('u_perm_') or k.startswith('g_perm_'):
                    obj_type = k[0]
                    obj_id = k[7:]
                    update_type = {'u': 'user',
                                   'g': 'user_group'}[obj_type]

                    if obj_type == 'u' and safe_int(obj_id) == default_user_id:
                        if str2bool(value.get('repo_private')):
                            # prevent from updating default user permissions
                            # when this repository is marked as private
                            update_value = EMPTY_PERM

                    perm_updates.add(
                        (obj_id, update_value, update_type))

            value['perm_additions'] = []  # propagated later
            value['perm_updates'] = list(perm_updates)
            value['perm_deletions'] = list(perm_deletions)

            updates_map = dict(
                (x[0], (x[1], x[2])) for x in value['perm_updates'])
            # make sure Additions don't override updates.
            for member_id, perm, member_type in list(perm_additions):
                if member_id in updates_map:
                    perm = updates_map[member_id][0]
                value['perm_additions'].append((member_id, perm, member_type))

                # on new entries validate users they exist and they are active !
                # this leaves feedback to the form
                try:
                    if member_type == 'user':
                        User.query()\
                            .filter(User.active == true())\
                            .filter(User.user_id == member_id).one()
                    if member_type == 'user_group':
                        UserGroup.query()\
                            .filter(UserGroup.users_group_active == true())\
                            .filter(UserGroup.users_group_id == member_id)\
                            .one()

                except Exception:
                    log.exception('Updated permission failed: org_exc:')
                    msg = M(self, 'perm_new_member_type', state)
                    raise formencode.Invalid(
                        msg, value, state, error_dict={
                            'perm_new_member_name': msg}
                    )
            return value
    return _validator


def ValidPath(localizer):
    _ = localizer

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'invalid_path': _(u'This is not a valid path')
        }

        def validate_python(self, value, state):
            if not os.path.isdir(value):
                msg = M(self, 'invalid_path', state)
                raise formencode.Invalid(
                    msg, value, state, error_dict={'paths_root_path': msg}
                )
    return _validator


def UniqSystemEmail(localizer, old_data=None):
    _ = localizer
    old_data = old_data or {}

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'email_taken': _(u'This e-mail address is already taken')
        }

        def _to_python(self, value, state):
            return value.lower()

        def validate_python(self, value, state):
            if (old_data.get('email') or '').lower() != value:
                user = User.get_by_email(value, case_insensitive=True)
                if user:
                    msg = M(self, 'email_taken', state)
                    raise formencode.Invalid(
                        msg, value, state, error_dict={'email': msg}
                    )
    return _validator


def ValidSystemEmail(localizer):
    _ = localizer

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'non_existing_email': _(u'e-mail "%(email)s" does not exist.')
        }

        def _to_python(self, value, state):
            return value.lower()

        def validate_python(self, value, state):
            user = User.get_by_email(value, case_insensitive=True)
            if user is None:
                msg = M(self, 'non_existing_email', state, email=value)
                raise formencode.Invalid(
                    msg, value, state, error_dict={'email': msg}
                )
    return _validator


def NotReviewedRevisions(localizer, repo_id):
    _ = localizer
    class _validator(formencode.validators.FancyValidator):
        messages = {
            'rev_already_reviewed':
                _(u'Revisions %(revs)s are already part of pull request '
                  u'or have set status'),
        }

        def validate_python(self, value, state):
            # check revisions if they are not reviewed, or a part of another
            # pull request
            statuses = ChangesetStatus.query()\
                .filter(ChangesetStatus.revision.in_(value))\
                .filter(ChangesetStatus.repo_id == repo_id)\
                .all()

            errors = []
            for status in statuses:
                if status.pull_request_id:
                    errors.append(['pull_req', status.revision[:12]])
                elif status.status:
                    errors.append(['status', status.revision[:12]])

            if errors:
                revs = ','.join([x[1] for x in errors])
                msg = M(self, 'rev_already_reviewed', state, revs=revs)
                raise formencode.Invalid(
                    msg, value, state, error_dict={'revisions': revs})

    return _validator


def ValidIp(localizer):
    _ = localizer

    class _validator(CIDR):
        messages = {
            'badFormat': _(u'Please enter a valid IPv4 or IpV6 address'),
            'illegalBits': _(
                u'The network size (bits) must be within the range '
                u'of 0-32 (not %(bits)r)'),
        }

        # we ovveride the default to_python() call
        def to_python(self, value, state):
            v = super(_validator, self).to_python(value, state)
            v = safe_unicode(v.strip())
            net = ipaddress.ip_network(address=v, strict=False)
            return str(net)

        def validate_python(self, value, state):
            try:
                addr = safe_unicode(value.strip())
                # this raises an ValueError if address is not IpV4 or IpV6
                ipaddress.ip_network(addr, strict=False)
            except ValueError:
                raise formencode.Invalid(self.message('badFormat', state),
                                         value, state)
    return _validator


def FieldKey(localizer):
    _ = localizer

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'badFormat': _(
                u'Key name can only consist of letters, '
                u'underscore, dash or numbers'),
        }

        def validate_python(self, value, state):
            if not re.match('[a-zA-Z0-9_-]+$', value):
                raise formencode.Invalid(self.message('badFormat', state),
                                         value, state)
    return _validator


def ValidAuthPlugins(localizer):
    _ = localizer

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'import_duplicate': _(
                u'Plugins %(loaded)s and %(next_to_load)s '
                u'both export the same name'),
            'missing_includeme': _(
                u'The plugin "%(plugin_id)s" is missing an includeme '
                u'function.'),
            'import_error': _(
                u'Can not load plugin "%(plugin_id)s"'),
            'no_plugin': _(
                u'No plugin available with ID "%(plugin_id)s"'),
        }

        def _to_python(self, value, state):
            # filter empty values
            return filter(lambda s: s not in [None, ''], value)

        def _validate_legacy_plugin_id(self, plugin_id, value, state):
            """
            Validates that the plugin import works. It also checks that the
            plugin has an includeme attribute.
            """
            try:
                plugin = _import_legacy_plugin(plugin_id)
            except Exception as e:
                log.exception(
                    'Exception during import of auth legacy plugin "{}"'
                    .format(plugin_id))
                msg = M(self, 'import_error', state, plugin_id=plugin_id)
                raise formencode.Invalid(msg, value, state)

            if not hasattr(plugin, 'includeme'):
                msg = M(self, 'missing_includeme', state, plugin_id=plugin_id)
                raise formencode.Invalid(msg, value, state)

            return plugin

        def _validate_plugin_id(self, plugin_id, value, state):
            """
            Plugins are already imported during app start up. Therefore this
            validation only retrieves the plugin from the plugin registry and
            if it returns something not None everything is OK.
            """
            plugin = loadplugin(plugin_id)

            if plugin is None:
                msg = M(self, 'no_plugin', state, plugin_id=plugin_id)
                raise formencode.Invalid(msg, value, state)

            return plugin

        def validate_python(self, value, state):
            unique_names = {}
            for plugin_id in value:

                # Validate legacy or normal plugin.
                if plugin_id.startswith(legacy_plugin_prefix):
                    plugin = self._validate_legacy_plugin_id(
                        plugin_id, value, state)
                else:
                    plugin = self._validate_plugin_id(plugin_id, value, state)

                # Only allow unique plugin names.
                if plugin.name in unique_names:
                    msg = M(self, 'import_duplicate', state,
                            loaded=unique_names[plugin.name],
                            next_to_load=plugin)
                    raise formencode.Invalid(msg, value, state)
                unique_names[plugin.name] = plugin
    return _validator


def ValidPattern(localizer):
    _ = localizer

    class _validator(formencode.validators.FancyValidator):
        messages = {
            'bad_format': _(u'Url must start with http or /'),
        }

        def _to_python(self, value, state):
            patterns = []

            prefix = 'new_pattern'
            for name, v in value.iteritems():
                pattern_name = '_'.join((prefix, 'pattern'))
                if name.startswith(pattern_name):
                    new_item_id = name[len(pattern_name)+1:]

                    def _field(name):
                        return '%s_%s_%s' % (prefix, name, new_item_id)

                    values = {
                        'issuetracker_pat': value.get(_field('pattern')),
                        'issuetracker_url': value.get(_field('url')),
                        'issuetracker_pref': value.get(_field('prefix')),
                        'issuetracker_desc': value.get(_field('description'))
                    }
                    new_uid = md5(values['issuetracker_pat'])

                    has_required_fields = (
                        values['issuetracker_pat']
                        and values['issuetracker_url'])

                    if has_required_fields:
                        # validate url that it starts with http or /
                        # otherwise it can lead to JS injections
                        # e.g specifig javascript:<malicios code>
                        if not values['issuetracker_url'].startswith(('http', '/')):
                            raise formencode.Invalid(
                                self.message('bad_format', state),
                                value, state)

                        settings = [
                            ('_'.join((key, new_uid)), values[key], 'unicode')
                            for key in values]
                        patterns.append(settings)

            value['patterns'] = patterns
            delete_patterns = value.get('uid') or []
            if not isinstance(delete_patterns, (list, tuple)):
                delete_patterns = [delete_patterns]
            value['delete_patterns'] = delete_patterns
            return value
    return _validator
